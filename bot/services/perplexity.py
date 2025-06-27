import httpx
from typing import List, Dict
from datetime import datetime

from bot.config import settings, PERPLEXITY_ENABLED
from bot.database.models import User, Answer, Question

from bot.prompts.base import BasePrompts
from bot.prompts.psychology import PsychologyPrompts
from .pdf_service import ReportGenerator


class PerplexityAIService:
    """Сервис для работы с Perplexity AI"""

    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.model = settings.PERPLEXITY_MODEL
        self.api_url = "https://api.perplexity.ai/chat/completions"

        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY не найден в настройках")

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
            "max_tokens": 4000,  # Увеличено для контекстного анализа с памятью (было 2000)
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
                raise Exception(
                    f"API Error {response.status_code}: {response.text}")

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

    async def analyze_user_responses(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Анализ ответов пользователя через Perplexity AI с контекстной памятью"""

        # Формируем данные для анализа
        user_data = self._prepare_user_data(user, questions, answers)

        try:
            print(
                f"🧠 Запускаем КОНТЕКСТНЫЙ AI анализ для пользователя {user.telegram_id}...")

            # 1️⃣ ЭТАП: Инициализация conversation с базовой ролью
            conversation = []

            # Устанавливаем роль эксперта-психолога
            conversation.append({
                "role": "system",
                "content": BasePrompts.get_common_context()
            })

            # Предоставляем данные для изучения
            conversation.append({
                "role": "user",
                "content": f"""Вот данные для психологического анализа:

{user_data}

Пожалуйста, изучите эти ответы и подтвердите готовность к созданию подробного психологического анализа. ВАЖНО: В дальнейших ответах обращайтесь к человеку напрямую через "ВЫ", "ВАШИ", "ВАМ" - НЕ используйте слова "пользователь" или "клиент"."""
            })

            # 2️⃣ ЭТАП: Первичное изучение данных
            print(f"🔄 Этап 1: ИИ изучает ответы...")
            initial_response = await self._make_api_request(conversation)

            conversation.append({
                "role": "assistant",
                "content": initial_response["content"]
            })

            print(
                f"📝 Первичный анализ получен: {len(initial_response['content'])} символов")

            # 3️⃣ ЭТАП: Генерация каждой страницы с накопленным контекстом
            results = {}
            page_names = {
                "page3": "Тип личности",
                "page4": "Мышление и решения",
                "page5": "Ограничивающие паттерны"
            }

            for page_type in ["page3", "page4", "page5"]:
                print(
                    f"🔄 Этап {len(results) + 2}: Генерация страницы '{page_names[page_type]}'...")

                # Добавляем запрос на конкретную страницу
                page_prompt = self._get_page_specific_prompt(page_type)
                conversation.append({
                    "role": "user",
                    "content": page_prompt
                })

                # Получаем ответ с полным контекстом предыдущих взаимодействий
                page_response = await self._make_api_request(conversation)

                # Сохраняем результат
                results[page_type] = page_response

                # Добавляем ответ в контекст для следующих запросов
                conversation.append({
                    "role": "assistant",
                    "content": page_response["content"]
                })

                content_length = len(page_response["content"])
                print(
                    f"📝 {page_names[page_type]}: получен ответ длиной {content_length} символов")

            # 4️⃣ ЭТАП: Финальная статистика
            page3_length = len(results["page3"]["content"])
            page4_length = len(results["page4"]["content"])
            page5_length = len(results["page5"]["content"])

            print(
                f"📈 СТАТИСТИКА КОНТЕКСТНОГО АНАЛИЗА для пользователя {user.telegram_id}:")
            print(f"   Страница 3 (Тип личности): {page3_length} символов")
            print(
                f"   Страница 4 (Мышление и решения): {page4_length} символов")
            print(
                f"   Страница 5 (Ограничивающие паттерны): {page5_length} символов")
            print(
                f"   Общий объем: {page3_length + page4_length + page5_length} символов")
            print(
                f"   📞 Всего обращений к ИИ: {len(results) + 1} (1 первичный + 3 страницы)")

            # Проверяем соответствие требуемому диапазону
            target_min, target_max = 1900, 2000

            for page_type, page_name in page_names.items():
                length = len(results[page_type]["content"])
                if length < target_min:
                    print(
                        f"⚠️ {page_name}: {length} символов - МЕНЬШЕ целевого диапазона ({target_min}-{target_max})")
                elif length > target_max:
                    print(
                        f"⚠️ {page_name}: {length} символов - БОЛЬШЕ целевого диапазона ({target_min}-{target_max})")
                else:
                    print(
                        f"✅ {page_name}: {length} символов - В ЦЕЛЕВОМ диапазоне ({target_min}-{target_max})")

            return {
                "success": True,
                "page3_analysis": results["page3"]["content"],
                "page4_analysis": results["page4"]["content"],
                "page5_analysis": results["page5"]["content"],
                # Новое: первичный анализ
                "initial_analysis": initial_response["content"],
                "usage": {
                    "initial": initial_response.get("usage", {}),
                    "page3": results["page3"].get("usage", {}),
                    "page4": results["page4"].get("usage", {}),
                    "page5": results["page5"].get("usage", {})
                },
                "character_stats": {
                    "page3_length": page3_length,
                    "page4_length": page4_length,
                    "page5_length": page5_length,
                    "total_length": page3_length + page4_length + page5_length,
                    "initial_length": len(initial_response["content"]),
                    "context_enabled": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"❌ Ошибка в контекстном анализе: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _get_page_specific_prompt(self, page_type: str) -> str:
        """Получить специфичный промпт для страницы из модуля psychology.py"""
        prompts_map = PsychologyPrompts.get_context_prompts_map()
        
        if page_type not in prompts_map:
            raise ValueError(f"Неизвестный тип страницы: {page_type}")
        
        return prompts_map[page_type]()


class AIAnalysisService:
    """Основной сервис для AI анализа"""

    def __init__(self):
        """Инициализация сервиса для AI анализа"""
        self.perplexity_enabled = PERPLEXITY_ENABLED

        if self.perplexity_enabled:
            try:
                self.ai_service = PerplexityAIService()
            except Exception as e:
                print(
                    f"⚠️ Ошибка инициализации Perplexity AI (отключаем): {e}")
                self.perplexity_enabled = False
                self.ai_service = None
        else:
            self.ai_service = None

        self.report_generator = ReportGenerator()

    async def generate_psychological_report(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Генерация полного психологического отчета с тремя страницами анализа"""

        try:
            if self.perplexity_enabled and self.ai_service:
                # 🧠 Контекстный анализ с памятью (единственный режим)
                print(
                    f"🧠 Запускаем AI анализ для пользователя {user.telegram_id}...")
                analysis_result = await self.ai_service.analyze_user_responses(user, questions, answers)

                if not analysis_result.get("success"):
                    print(f"⚠️ AI анализ неудачен, создаем отчет без анализа")
                    analysis_result = self._create_fallback_analysis()
            else:
                print(
                    f"ℹ️ Perplexity AI отключен, создаем отчет без анализа для пользователя {user.telegram_id}")
                analysis_result = self._create_fallback_analysis()

            # Создаем PDF отчет
            print(f"📄 Создаем PDF отчет...")
            report_filepath = self.report_generator.create_pdf_report(
                user, analysis_result)

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
        print(
            f"   Страница 5 (Ограничивающие паттерны): {page5_length} символов")
        print(
            f"   Общий объем: {page3_length + page4_length + page5_length} символов")
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
