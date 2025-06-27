import httpx
from typing import List, Dict
from datetime import datetime

from bot.config import settings, PERPLEXITY_ENABLED
from bot.database.models import User, Answer, Question
from bot.prompts import PsychologyPrompts
from .pdf_service import ReportGenerator


class PerplexityAIService:
    """Сервис для работы с Perplexity AI"""
    
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.model = settings.PERPLEXITY_MODEL
        self.api_url = "https://api.perplexity.ai/chat/completions"
        
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY не найден в настройках")
    


    async def analyze_user_responses(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Анализ ответов пользователя через Perplexity AI для всех трех страниц"""
        
        # Формируем данные для анализа
        user_data = self._prepare_user_data(user, questions, answers)
        
        try:
            # Генерируем анализ для каждой страницы
            print(f"📊 Генерируем анализ для пользователя {user.telegram_id}...")
            
            page3_result = await self._generate_page_analysis(user, user_data, "page3")
            page4_result = await self._generate_page_analysis(user, user_data, "page4") 
            page5_result = await self._generate_page_analysis(user, user_data, "page5")
            
            # Логируем общую статистику символов
            page3_length = len(page3_result.get("content", ""))
            page4_length = len(page4_result.get("content", ""))
            page5_length = len(page5_result.get("content", ""))
            
            print(f"📈 СТАТИСТИКА СИМВОЛОВ для пользователя {user.telegram_id}:")
            print(f"   Страница 3 (Тип личности): {page3_length} символов")
            print(f"   Страница 4 (Мышление и решения): {page4_length} символов") 
            print(f"   Страница 5 (Ограничивающие паттерны): {page5_length} символов")
            print(f"   Общий объем: {page3_length + page4_length + page5_length} символов")
            
            # Проверяем соответствие требуемому диапазону 1900-2000 символов
            target_min, target_max = 1900, 2000
            
            for page_name, length in [("Страница 3", page3_length), ("Страница 4", page4_length), ("Страница 5", page5_length)]:
                if length < target_min:
                    print(f"⚠️ {page_name}: {length} символов - МЕНЬШЕ целевого диапазона ({target_min}-{target_max})")
                elif length > target_max:
                    print(f"⚠️ {page_name}: {length} символов - БОЛЬШЕ целевого диапазона ({target_min}-{target_max})")
                else:
                    print(f"✅ {page_name}: {length} символов - В ЦЕЛЕВОМ диапазоне ({target_min}-{target_max})")
            
            return {
                "success": True,
                "page3_analysis": page3_result.get("content", ""),
                "page4_analysis": page4_result.get("content", ""),
                "page5_analysis": page5_result.get("content", ""),
                "usage": {
                    "page3": page3_result.get("usage", {}),
                    "page4": page4_result.get("usage", {}),
                    "page5": page5_result.get("usage", {})
                },
                "character_stats": {
                    "page3_length": page3_length,
                    "page4_length": page4_length,
                    "page5_length": page5_length,
                    "total_length": page3_length + page4_length + page5_length
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _generate_page_analysis(self, user: User, user_data: str, page_type: str) -> Dict:
        """Генерация анализа для конкретной страницы"""
        
        # Получаем промпт из модуля промптов
        prompts_map = PsychologyPrompts.get_prompts_map()
        if page_type not in prompts_map:
            raise ValueError(f"Неизвестный тип страницы: {page_type}")
        
        system_prompt = prompts_map[page_type]()
        
        # Формируем пользовательский промпт из шаблона
        user_prompt = PsychologyPrompts.get_user_info_template().format(
            user_data=user_data
        )
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        
        print(f"🔄 Генерируем анализ для {page_type}...")
        result = await self._make_api_request(messages)
        
        # Логируем длину ответа для конкретной страницы
        content_length = len(result.get("content", ""))
        page_names = {
            "page3": "Тип личности", 
            "page4": "Мышление и решения",
            "page5": "Ограничивающие паттерны"
        }
        page_name = page_names.get(page_type, page_type)
        
        print(f"📝 {page_name}: получен ответ длиной {content_length} символов")
        
        return result

    def _prepare_user_data(self, user: User, questions: List[Question], answers: List[Answer]) -> str:
        """Подготовка данных пользователя для анализа"""
        
        # Создаем словарь вопрос-ответ
        qa_pairs = []
        answer_dict = {ans.question_id: ans for ans in answers}
        
        for question in questions:
            answer = answer_dict.get(question.id)
            if answer and answer.text_answer:
                qa_pairs.append(f"""
Вопрос {question.order_number}: {question.text}
Ответ: {answer.text_answer}
""")
        
        return "\n".join(qa_pairs)
    
    async def _make_api_request(self, messages: List[Dict]) -> Dict:
        """Выполнение запроса к Perplexity API"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PRIZMA-AI-Psychologist/1.0"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 2000,  # Достаточно для детального анализа
            "temperature": 0.7,  # Баланс между креативностью и точностью
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Извлекаем ответ
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                
                return {
                    "content": content,
                    "usage": usage
                }
            else:
                raise Exception("Неожиданный формат ответа от API")




class AIAnalysisService:
    """Основной сервис для AI анализа"""
    
    def __init__(self):
        self.perplexity_enabled = PERPLEXITY_ENABLED
        if self.perplexity_enabled:
            try:
                self.ai_service = PerplexityAIService()
            except Exception as e:
                print(f"⚠️ Ошибка инициализации Perplexity AI (отключаем): {e}")
                self.perplexity_enabled = False
                self.ai_service = None
        else:
            self.ai_service = None
        
        self.report_generator = ReportGenerator()
    
    async def generate_psychological_report(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Генерация полного психологического отчета с тремя страницами анализа"""
        
        try:
            if self.perplexity_enabled and self.ai_service:
                # Анализируем ответы через AI для всех трех страниц
                print(f"🧠 Запускаем AI анализ для пользователя {user.telegram_id}...")
                analysis_result = await self.ai_service.analyze_user_responses(user, questions, answers)
                
                if not analysis_result.get("success"):
                    print(f"⚠️ AI анализ неудачен, создаем отчет без анализа")
                    analysis_result = self._create_fallback_analysis()
            else:
                print(f"ℹ️ Perplexity AI отключен, создаем отчет без анализа для пользователя {user.telegram_id}")
                analysis_result = self._create_fallback_analysis()
            
            # Создаем PDF отчет
            print(f"📄 Создаем PDF отчет...")
            report_filepath = self.report_generator.create_pdf_report(user, analysis_result)
            
            print(f"✅ Отчет успешно создан: {report_filepath}")
            
            return {
                "success": True,
                "page3_analysis": analysis_result["page3_analysis"],
                "page4_analysis": analysis_result["page4_analysis"], 
                "page5_analysis": analysis_result["page5_analysis"],
                "report_file": report_filepath,
                "usage": analysis_result.get("usage", {}),
                "character_stats": analysis_result.get("character_stats", {}),
                "timestamp": analysis_result["timestamp"]
            }
            
        except Exception as e:
            print(f"❌ Ошибка при генерации отчета: {e}")
            return {
                "success": False,
                "error": str(e),
                "stage": "general"
            }
    
    def _create_fallback_analysis(self) -> Dict:
        """Создать базовый анализ без ИИ"""
        timestamp = datetime.utcnow().isoformat()
        
        # Создаем fallback тексты
        page3_analysis = "Ваши ответы показывают уникальные особенности личности. Детальный анализ будет добавлен в ближайшее время."
        page4_analysis = "На основе ваших ответов можно выделить несколько ключевых характеристик вашего психологического профиля."
        page5_analysis = "Рекомендации по развитию и самосовершенствованию будут предоставлены в обновленной версии отчета."
        
        # Логируем статистику символов для fallback анализа
        page3_length = len(page3_analysis)
        page4_length = len(page4_analysis)
        page5_length = len(page5_analysis)
        
        print(f"📈 СТАТИСТИКА СИМВОЛОВ для fallback анализа:")
        print(f"   Страница 3 (Тип личности): {page3_length} символов")
        print(f"   Страница 4 (Мышление и решения): {page4_length} символов") 
        print(f"   Страница 5 (Ограничивающие паттерны): {page5_length} символов")
        print(f"   Общий объем: {page3_length + page4_length + page5_length} символов")
        print(f"⚠️ ВНИМАНИЕ: Используется fallback анализ - все тексты НЕ соответствуют целевому объему 1900-2000 символов")
        
        return {
            "success": True,
            "page3_analysis": page3_analysis,
            "page4_analysis": page4_analysis,
            "page5_analysis": page5_analysis,
            "usage": {},
            "character_stats": {
                "page3_length": page3_length,
                "page4_length": page4_length,
                "page5_length": page5_length,
                "total_length": page3_length + page4_length + page5_length,
                "is_fallback": True
            },
            "timestamp": timestamp
        } 