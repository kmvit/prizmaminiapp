import asyncio
import httpx
from typing import List, Dict
from datetime import datetime

from bot.config import settings, PERPLEXITY_ENABLED
from bot.database.models import User, Answer, Question

from bot.prompts.base import BasePrompts
from bot.prompts.psychology import PsychologyPrompts
from bot.prompts.premium_new import PremiumPromptsNew
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

    async def _make_api_request(self, messages: List[Dict], is_premium: bool = False, retry_count: int = 3) -> Dict:
        """Выполнение запроса к Perplexity API с retry логикой"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PRIZMA-AI-Psychologist/1.0"
        }

        # Настраиваем max_tokens - увеличиваем для премиум анализа
        if is_premium:
            # Увеличиваем лимит для генерации больших разделов
            max_tokens = 12000  # Увеличено для генерации 6-10 страниц за раз
        else:
            max_tokens = 4000

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens, 
            "temperature": 0.6,  # Баланс между креативностью и точностью
            "stream": False
        }
        
        # Логируем информацию о запросе
        if is_premium:
            print(f"🔧 API запрос: max_tokens={max_tokens}")
            estimated_input_tokens = self._estimate_token_count(''.join([msg.get('content', '') for msg in messages]))
            print(f"🔧 Оценка входящих токенов: {estimated_input_tokens}")

        # Retry логика с экспоненциальными задержками
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=600.0) as client:  # Увеличиваем timeout до 10 минут
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=payload
                    )

                    if response.status_code != 200:
                        error_msg = f"API Error {response.status_code}: {response.text}"
                        print(f"❌ {error_msg}")
                        
                        # Если это rate limiting, ждем дольше
                        if response.status_code == 429:
                            wait_time = (2 ** attempt) * 10  # 10, 20, 40 секунд
                            print(f"⏳ Rate limit, ждем {wait_time} секунд...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(error_msg)

                    result = response.json()

                    # Извлекаем ответ
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        usage = result.get("usage", {})
                        
                        # Проверяем минимальный размер ответа для премиум запросов
                        if is_premium and len(content.strip()) < 200:
                            error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: API вернул слишком короткий ответ ({len(content.strip())} символов). Ожидалось минимум 1000 символов. Это указывает на ошибку в генерации."
                            print(error_msg)
                            print(f"🔧 Первые 200 символов ответа: {content[:200]}...")
                            raise ValueError(error_msg)
                                                # Логируем информацию об ответе для премиум запросов
                        if is_premium:
                            content_length = len(content)
                            finish_reason = result["choices"][0].get("finish_reason", "unknown")
                            print(f"🔧 API ответ: {content_length} символов, finish_reason='{finish_reason}'")
                            if usage:
                                print(f"🔧 Использование токенов: {usage}")
                            
                            if attempt > 0:
                                print(f"✅ Успешно после {attempt + 1} попыток")

                        return {
                            "content": content,
                            "usage": usage
                        }
                    else:
                        raise Exception("Неожиданный формат ответа от API")
                        
            except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError) as e:
                wait_time = (2 ** attempt) * 5  # 5, 10, 20 секунд
                print(f"🔄 Попытка {attempt + 1}/{retry_count} неудачна: {e}")
                
                if attempt < retry_count - 1:
                    print(f"⏳ Ждем {wait_time} секунд перед повтором...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Все {retry_count} попыток исчерпаны")
                    raise e
            except Exception as e:
                print(f"❌ Неожиданная ошибка: {e}")
                raise e

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

            for i, page_type in enumerate(["page3", "page4", "page5"]):
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
                
                # Пауза между запросами для стабильности API (кроме последнего)
                if i < 2:  # Если это не последняя страница (page5)
                    wait_time = 5  # 5 секунд между запросами
                    print(f"⏳ Пауза {wait_time} секунд для стабильности API...")
                    await asyncio.sleep(wait_time)

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

    async def analyze_premium_responses(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Платный анализ ответов пользователя через Perplexity AI (50 вопросов) - ПОСТРАНИЧНАЯ ГЕНЕРАЦИЯ"""

        # Формируем данные для анализа
        user_data = self._prepare_user_data(user, questions, answers)

        try:
            print(f"🧠 Запускаем ПОСТРАНИЧНЫЙ ПЛАТНЫЙ AI анализ для пользователя {user.telegram_id}...")
            print(f"📄 Будет сгенерировано 63 страницы (10+5+7+7+8+6+8+6+6)")

            # 1️⃣ ЭТАП: Инициализация conversation ТОЛЬКО с базовой ролью
            conversation = []

            # Устанавливаем ТОЛЬКО базовую роль эксперта-психолога 
            conversation.append({
                "role": "system",
                "content": f"""{PremiumPromptsNew.get_base_prompt()}

ВАЖНО: Это базовые инструкции. Дополнительные инструкции для конкретных разделов будут предоставлены по мере необходимости."""
            })

            # Предоставляем данные для изучения (50 вопросов)
            conversation.append({
                "role": "user",
                "content": f"""Вот данные для ПЛАТНОГО психологического анализа (50 вопросов):

{user_data}

Пожалуйста, изучите эти ответы и подтвердите готовность к созданию подробного ПЛАТНОГО психологического анализа. ВАЖНО: В дальнейших ответах обращайтесь к человеку напрямую через "ВЫ", "ВАШИ", "ВАМ" - НЕ используйте слова "пользователь" или "клиент"."""
            })

            # 2️⃣ ЭТАП: Первичное изучение данных
            print(f"🔄 Этап 1: ИИ изучает 50 ответов...")
            initial_response = await self._make_api_request(conversation, is_premium=True)

            conversation.append({
                "role": "assistant",
                "content": initial_response["content"]
            })

            print(f"📝 Первичный анализ получен: {len(initial_response['content'])} символов")

            # 3️⃣ ЭТАП: ПОСТРАНИЧНАЯ генерация всех 63 страниц
            all_pages = {}
            all_individual_pages = {}  # Новая структура для отдельных страниц
            
            # Определяем структуру страниц согласно новым промптам
            page_structure = [
                ("premium_analysis", "Психологический портрет", 10),
                ("premium_strengths", "Сильные стороны и таланты", 5),
                ("premium_growth_zones", "Зоны роста", 7),
                ("premium_compensation", "Компенсаторика", 7),
                ("premium_interaction", "Взаимодействие с окружающими", 8),
                ("premium_prognosis", "Прогностика", 6),
                ("premium_practical", "Практическое приложение", 8),
                ("premium_conclusion", "Заключение", 6),
                ("premium_appendix", "Приложения", 6)
            ]
            
            page_counter = 1
            total_api_calls = 1  # Первичный анализ
            
            for section_key, section_name, page_count in page_structure:
                print(f"\n🔄 РАЗДЕЛ: {section_name} ({page_count} страниц)")
                section_pages = {}
                
                # 🎯 ДОБАВЛЯЕМ ПРОМПТ РАЗДЕЛА ТОЛЬКО при входе в новый раздел
                section_prompt = self._get_section_prompt(section_key)
                conversation.append({
                    "role": "user",
                    "content": f"""Переходим к разделу "{section_name}". Вот специальные инструкции для этого раздела:

{section_prompt}

Используйте эти инструкции для всех страниц данного раздела."""
                })
                
                # Получаем подтверждение от ИИ
                section_response = await self._make_api_request(conversation, is_premium=True)
                conversation.append({
                    "role": "assistant", 
                    "content": section_response["content"]
                })
                
                print(f"✅ Инструкции раздела получены и обработаны")
                total_api_calls += 1
                
                for page_num in range(1, page_count + 1):
                    print(f"📄 Генерация страницы {page_counter} ({section_name}, стр. {page_num}/{page_count})...")
                    
                    # Мониторинг и урезание контекста для премиум отчетов
                    current_tokens = self._estimate_conversation_tokens(conversation)
                    if current_tokens > 50000:  # Урезаем гораздо раньше (~50k токенов)
                        conversation = self._trim_conversation_context(conversation, max_tokens=30000)
                        trimmed_tokens = self._estimate_conversation_tokens(conversation)
                        print(f"📊 Контекст после урезания: {trimmed_tokens} токенов (было {current_tokens})")
                    
                    # Создаем промпт для конкретной страницы
                    page_prompt, expected_pages = self._get_premium_page_prompt(section_key, page_num, page_count)
                    
                    conversation.append({
                        "role": "user", 
                        "content": page_prompt
                    })
                    
                    # Генерируем страницу
                    page_response = await self._make_api_request(conversation, is_premium=True)
                    
                    # Сохраняем результат
                    page_key = f"{section_key}_page_{page_num}"
                    section_pages[page_key] = page_response["content"]
                    
                    # Сохраняем в индивидуальные страницы
                    all_individual_pages[f"page_{page_counter:02d}"] = {
                        "content": page_response["content"],
                        "section": section_name,
                        "section_key": section_key,
                        "page_num": page_num,
                        "global_page": page_counter
                    }
                    
                    # Добавляем в контекст
                    conversation.append({
                        "role": "assistant",
                        "content": page_response["content"]
                    })
                    
                    page_length = len(page_response["content"])
                    conversation_tokens = self._estimate_conversation_tokens(conversation)
                    print(f"   ✅ Страница {page_counter}: {page_length} символов (контекст: ~{conversation_tokens} токенов)")
                    
                    page_counter += 1
                    total_api_calls += 1
                
                # Объединяем страницы раздела
                all_pages[section_key] = "\n\n".join(section_pages.values())
                section_length = len(all_pages[section_key])
                print(f"📊 {section_name}: {section_length} символов ({page_count} страниц)")

            # 4️⃣ ЭТАП: Финальная статистика
            total_length = sum(len(content) for content in all_pages.values())
            
            print(f"\n📈 СТАТИСТИКА ПОСТРАНИЧНОГО АНАЛИЗА для пользователя {user.telegram_id}:")
            for section_key, section_name, page_count in page_structure:
                length = len(all_pages[section_key])
                avg_per_page = length / page_count
                print(f"   {section_name}: {length} символов ({page_count} страниц, ~{avg_per_page:.0f} символов/страница)")
            print(f"   Общий объем: {total_length} символов")
            print(f"   📞 Всего обращений к ИИ: {total_api_calls} (1 первичный + 9 инструкций разделов + 63 страницы)")
            print(f"   📄 Всего страниц: 63")
            print(f"   ⚡ НОВАЯ АРХИТЕКТУРА: промпты разделов загружаются по мере необходимости!")

            return {
                "success": True,
                "premium_analysis": all_pages["premium_analysis"],
                "premium_strengths": all_pages["premium_strengths"],
                "premium_growth_zones": all_pages["premium_growth_zones"],
                "premium_compensation": all_pages["premium_compensation"],
                "premium_interaction": all_pages["premium_interaction"],
                "premium_prognosis": all_pages["premium_prognosis"],
                "premium_practical": all_pages["premium_practical"],
                "premium_conclusion": all_pages["premium_conclusion"],
                "premium_appendix": all_pages["premium_appendix"],
                "individual_pages": all_individual_pages,  # Новое поле с отдельными страницами
                "initial_analysis": initial_response["content"],
                "usage": {
                    "initial": initial_response.get("usage", {}),
                    "total_api_calls": total_api_calls,
                    "pages_generated": 63
                },
                "character_stats": {
                    "total_length": total_length,
                    "initial_length": len(initial_response["content"]),
                    "pages_count": 63,
                    "context_enabled": True,
                    "is_premium": True,
                    "is_paginated": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"❌ Ошибка в постраничном анализе: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def analyze_premium_responses_optimized(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Оптимизированный платный анализ: 9 запросов вместо 74 с маркерами страниц"""

        # Формируем данные для анализа
        user_data = self._prepare_user_data(user, questions, answers)

        try:
            print(f"🧠 Запускаем ОПТИМИЗИРОВАННЫЙ платный анализ для пользователя {user.telegram_id}...")
            print(f"📄 Будет сгенерировано 63 страницы за 9 запросов")

            # Структура разделов
            sections = [
                ("premium_analysis", "Психологический портрет", 10),
                ("premium_strengths", "Сильные стороны и таланты", 5),
                ("premium_growth_zones", "Зоны роста", 7),
                ("premium_compensation", "Компенсаторика", 7),
                ("premium_interaction", "Взаимодействие с окружающими", 8),
                ("premium_prognosis", "Прогностика", 6),
                ("premium_practical", "Практическое приложение", 8),
                ("premium_conclusion", "Заключение", 6),
                ("premium_appendix", "Приложения", 6)
            ]
            
            all_pages = {}
            all_individual_pages = {}
            page_counter = 1
            total_api_calls = 0
            
            for section_key, section_name, page_count in sections:
                print(f"\n🔄 Генерируем раздел: {section_name} ({page_count} страниц)")
                print(f"⏱️ Начинаем запрос к API...")
                
                # Создаем промпт с маркерами страниц
                section_prompt = self._create_section_prompt_with_markers(
                    section_key, section_name, page_count, user_data
                )
                
                # ОДИН запрос на весь раздел
                start_time = datetime.utcnow()
                response = await self._make_api_request([{
                    "role": "user",
                    "content": section_prompt
                }], is_premium=True)
                end_time = datetime.utcnow()
                
                request_duration = (end_time - start_time).total_seconds()
                print(f"⏱️ Запрос завершен за {request_duration:.1f} секунд")
                
                total_api_calls += 1
                
                # Парсим ответ на отдельные страницы
                try:
                    section_pages = self._parse_section_response(
                        response["content"], section_key, section_name, page_count, page_counter
                    )
                except ValueError as e:
                    # Если парсинг не удался из-за короткого ответа, останавливаем весь процесс
                    print(f"❌ Остановка генерации отчета из-за ошибки в разделе '{section_name}': {e}")
                    raise e
                
                # Сохраняем результаты
                section_contents = [page_data["content"] for page_data in section_pages.values()]
                all_pages[section_key] = "\n\n".join(section_contents)
                all_individual_pages.update(section_pages)
                
                page_counter += page_count
                
                section_length = len(all_pages[section_key])
                print(f"✅ {section_name}: {section_length} символов ({page_count} страниц)")
                
                # Пауза между запросами для стабильности API (кроме последнего)
                if section_key != "premium_appendix":  # Если это не последний раздел
                    wait_time = 8  # 8 секунд между запросами
                    print(f"⏳ Пауза {wait_time} секунд для стабильности API...")
                    await asyncio.sleep(wait_time)

            # Финальная статистика
            total_length = sum(len(content) for content in all_pages.values())
            
            print(f"\n📈 СТАТИСТИКА ОПТИМИЗИРОВАННОГО АНАЛИЗА для пользователя {user.telegram_id}:")
            for section_key, section_name, page_count in sections:
                length = len(all_pages[section_key])
                avg_per_page = length / page_count
                print(f"   {section_name}: {length} символов ({page_count} страниц, ~{avg_per_page:.0f} символов/страница)")
            print(f"   Общий объем: {total_length} символов")
            print(f"   📞 Всего обращений к ИИ: {total_api_calls} (вместо 74!)")
            print(f"   📄 Всего страниц: 63")
            print(f"   ⚡ ОПТИМИЗАЦИЯ: 87% экономии запросов!")

            return {
                "success": True,
                "premium_analysis": all_pages["premium_analysis"],
                "premium_strengths": all_pages["premium_strengths"],
                "premium_growth_zones": all_pages["premium_growth_zones"],
                "premium_compensation": all_pages["premium_compensation"],
                "premium_interaction": all_pages["premium_interaction"],
                "premium_prognosis": all_pages["premium_prognosis"],
                "premium_practical": all_pages["premium_practical"],
                "premium_conclusion": all_pages["premium_conclusion"],
                "premium_appendix": all_pages["premium_appendix"],
                "individual_pages": all_individual_pages,
                "usage": {
                    "total_api_calls": total_api_calls,
                    "pages_generated": 63,
                    "optimization_ratio": "87%"
                },
                "character_stats": {
                    "total_length": total_length,
                    "pages_count": 63,
                    "context_enabled": True,
                    "is_premium": True,
                    "is_optimized": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError) as e:
            print(f"❌ Сетевая ошибка API: {e}")
            print(f"💡 Рекомендация: проверьте интернет-соединение и попробуйте позже")
            return {
                "success": False,
                "error": f"Ошибка API при генерации анализа: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        except ValueError as e:
            # Ошибки валидации (короткие ответы)
            print(f"❌ Ошибка валидации в оптимизированном анализе: {e}")
            return {
                "success": False,
                "error": f"Ошибка валидации: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"❌ Ошибка в оптимизированном анализе: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Ошибка API при генерации анализа: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _create_section_prompt_with_markers(self, section_key: str, section_name: str, page_count: int, user_data: str) -> str:
        """Создает промпт для раздела с маркерами страниц"""
        
        # Получаем структуру страниц раздела
        section_structure = self._get_section_structure(section_key)
        
        # Формируем список страниц с маркерами
        pages_list = []
        for i, subblock in enumerate(section_structure, 1):
            pages_list.append(f"=== СТРАНИЦА {i} ===\n{subblock}")
        
        pages_text = "\n\n".join(pages_list)
        
        prompt = f"""Создайте ПОЛНЫЙ раздел "{section_name}" ({page_count} страниц).

ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:
{user_data}

ИНСТРУКЦИИ РАЗДЕЛА:
{self._get_section_prompt(section_key)}

СТРУКТУРА СТРАНИЦ:
{pages_text}

🚨 КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:
- КАЖДАЯ страница ДОЛЖНА быть 2000-3000 символов (минимум 2000!)
- Используйте маркеры === СТРАНИЦА X === для разделения
- Обращение через "ВЫ", "ВАШИ", "ВАМ"
- Максимум 2-3 цитаты из ответов на страницу
- Создайте РОВНО {page_count} страниц согласно структуре
- НЕ ПРОПУСКАЙТЕ страницы и НЕ ОБЪЕДИНЯЙТЕ их!

📝 ФОРМАТ КАЖДОЙ СТРАНИЦЫ:
=== СТРАНИЦА X ===
# Заголовок страницы
Подробное содержание (минимум 2000 символов)
...

Начните с маркера === СТРАНИЦА 1 === и создайте ВСЕ {page_count} страниц раздела."""

        return prompt

    def _get_section_structure(self, section_key: str) -> List[str]:
        """Получает структуру страниц для раздела"""
        
        section_subblocks = {
            "premium_analysis": [
                "АНАЛИЗ BIG FIVE (1 страница)",
                "ОПРЕДЕЛЕНИЕ ТИПА MBTI (1 страница)", 
                "АРХЕТИПИЧЕСКАЯ СТРУКТУРА (1 страница)",
                "КОГНИТИВНЫЙ ПРОФИЛЬ (1 страница)",
                "ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ (1-2 страницы)",
                "СИСТЕМА ЦЕННОСТЕЙ (1 страница)",
                "КОММУНИКАТИВНЫЙ СТИЛЬ (1 страница)",
                "МОТИВАЦИОННЫЕ ДРАЙВЕРЫ (1 страница)",
                "ТЕНЕВЫЕ АСПЕКТЫ ЛИЧНОСТИ (1-2 страницы)",
                "ЭКЗИСТЕНЦИАЛЬНАЯ ИСПОЛНЕННОСТЬ (1-2 страницы)"
            ],
            "premium_strengths": [
                "ПРИРОДНЫЕ ТАЛАНТЫ (1,5 страницы)",
                "ПРИОБРЕТЁННЫЕ КОМПЕТЕНЦИИ (2 страницы)",
                "РЕСУРСНЫЕ СОСТОЯНИЯ (2 страницы)",
                "ПОТЕНЦИАЛ РАЗВИТИЯ (1 страница)",
                "УНИКАЛЬНЫЕ КОМБИНАЦИИ КАЧЕСТВ (1 страница)"
            ],
            "premium_growth_zones": [
                "ОГРАНИЧИВАЮЩИЕ УБЕЖДЕНИЯ (1 страница)",
                "ТРАНСФОРМАЦИЯ УБЕЖДЕНИЙ (0.5 страницы)",
                "КОГНИТИВНЫЕ ИСКАЖЕНИЯ (1 страница)",
                "СЛЕПЫЕ ЗОНЫ (1 страница)",
                "ЭМОЦИОНАЛЬНЫЕ ТРИГГЕРЫ (2 страницы)",
                "ПАТТЕРНЫ САМОСАБОТАЖА (1 страница)",
                "СОМАТИЧЕСКИЕ ПРОЯВЛЕНИЯ (1 страница)"
            ],
            "premium_compensation": [
                "СТРАТЕГИИ РАЗВИТИЯ (2 страницы)",
                "ТЕХНИКИ САМОРЕГУЛЯЦИИ (1 страница)",
                "АЛЬТЕРНАТИВНЫЕ МОДЕЛИ ПОВЕДЕНИЯ (1 страница)",
                "РЕСУРСЫ ВОССТАНОВЛЕНИЯ (1 страница)",
                "ИНДИВИДУАЛЬНЫЙ ПЛАН РАЗВИТИЯ (3 страницы)",
                "РЕКОМЕНДУЕМЫЕ ПРАКТИКИ (2 страницы)",
                "ОБРАЗНО-СИМВОЛИЧЕСКАЯ РАБОТА (1 страница)"
            ],
            "premium_interaction": [
                "СОВМЕСТИМОСТЬ (1 страница)",
                "СТРАТЕГИИ ДЛЯ СЛОЖНЫХ СОЧЕТАНИЙ (1 страница)",
                "ПЕРСОНАЛЬНЫЙ СТИЛЬ ОБЩЕНИЯ (1 страница)",
                "ТЕХНИКИ АДАПТИВНОЙ КОММУНИКАЦИИ (1 страница)",
                "РОЛЬ В КОМАНДЕ (1 страница)",
                "БЛИЗКИЕ ОТНОШЕНИЯ (1 страница)",
                "РАЗРЕШЕНИЕ КОНФЛИКТОВ (1 страница)",
                "СЕМЕЙНЫЕ ПАТТЕРНЫ И ГРАНИЦЫ (1 страница)"
            ],
            "premium_prognosis": [
                "ДВУХСЦЕНАРНЫЙ ПРОГНОЗ РАЗВИТИЯ (1 страница)",
                "КРИЗИСЫ И ТОЧКИ РОСТА (1 страница)",
                "САМОРЕАЛИЗАЦИЯ (1 страница)",
                "ПРОГНОЗ РАЗВИТИЯ КАЧЕСТВ (1 страница)",
                "ДОЛГОСРОЧНЫЕ ПЕРСПЕКТИВЫ (1 страница)"
            ],
            "premium_practical": [
                "ПРОФРЕАЛИЗАЦИЯ (2 страницы)",
                "ПРОДУКТИВНОСТЬ (2 страницы)",
                "ПРИНЯТИЕ РЕШЕНИЙ (2 страницы)",
                "СОЦИАЛЬНЫЕ НАВЫКИ (2 страницы)",
                "ЗДОРОВЬЕ И БЛАГОПОЛУЧИЕ (2 страницы)",
                "ТЕХНИКИ ДЛЯ СИЛЬНЫХ СТОРОН (1 страница)",
                "УПРАЖНЕНИЯ ДЛЯ ЗОН РОСТА (1 страница)",
                "ЧЕК-ЛИСТЫ И ТРЕКЕРЫ (1 страница)"
            ],
            "premium_conclusion": [
                "ОБОБЩЕНИЕ ИНСАЙТОВ (1 страница)",
                "СИНТЕЗ СИЛЬНЫХ СТОРОН (1 страница)",
                "МОТИВАЦИОННОЕ ПОСЛАНИЕ (1 страница)",
                "РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ (1 страница)",
                "ЭВОЛЮЦИЯ ЛИЧНОСТИ (1 страница)",
                "ФИНАЛЬНОЕ ПОСЛАНИЕ (1 страница)"
            ],
            "premium_appendix": [
                "ГЛОССАРИЙ ТЕРМИНОВ (1 страница)",
                "РЕКОМЕНДУЕМЫЕ РЕСУРСЫ (2 страницы)",
                "ВИЗУАЛИЗАЦИИ И ДИАГРАММЫ (1 страница)",
                "ПЕРСОНАЛЬНЫЕ АФФИРМАЦИИ (2 страницы)",
                "ШАБЛОНЫ ДЛЯ САМОАНАЛИЗА (1 страница)",
                "ПРОЕКТИВНЫЕ ОБРАЗЫ И МЕТАФОРЫ (1 страница)"
            ]
        }
        
        return section_subblocks.get(section_key, [])

    def _parse_section_response(self, response_content: str, section_key: str, section_name: str, page_count: int, start_page: int) -> Dict[str, str]:
        """Парсит ответ ИИ на отдельные страницы по маркерам"""
        
        pages = {}
        
        # Разделяем по маркерам === СТРАНИЦА X ===
        import re
        page_pattern = r'=== СТРАНИЦА (\d+) ===\s*(.*?)(?=\s*=== СТРАНИЦА \d+ ===|$)'
        matches = re.findall(page_pattern, response_content, re.DOTALL)
        
        if matches:
            # Обрабатываем найденные страницы
            for page_num_str, page_content in matches:
                page_num = int(page_num_str)
                global_page = start_page + page_num - 1
                
                # Очищаем контент от лишних пробелов
                clean_content = page_content.strip()
                
                if clean_content:
                    page_key = f"page_{global_page:02d}"
                    pages[page_key] = {
                        "content": clean_content,
                        "section": section_name,
                        "section_key": section_key,
                        "page_num": page_num,
                        "global_page": global_page
                    }
                    
                    print(f"   📄 Страница {global_page}: {len(clean_content)} символов")
        else:
            # Если маркеры не найдены, делим контент на равные части
            print(f"⚠️ Маркеры страниц не найдены, делим контент на {page_count} частей")
            content_length = len(response_content)
            part_length = content_length // page_count
            
            for i in range(page_count):
                start_pos = i * part_length
                end_pos = start_pos + part_length if i < page_count - 1 else content_length
                
                page_content = response_content[start_pos:end_pos].strip()
                global_page = start_page + i
                
                # Добавляем заголовок страницы если его нет
                if not page_content.startswith('#'):
                    page_content = f"# Страница {i + 1}\n\n{page_content}"
                
                page_key = f"page_{global_page:02d}"
                pages[page_key] = {
                    "content": page_content,
                    "section": section_name,
                    "section_key": section_key,
                    "page_num": i + 1,
                    "global_page": global_page
                }
                
                print(f"   📄 Страница {global_page}: {len(page_content)} символов")
        
        return pages

    def _get_premium_block_prompt(self, block_type: str) -> str:
        """Получить специфичный промпт для блока платной версии"""
        prompts_map = PremiumPromptsNew.get_context_prompts_map()
        
        if block_type not in prompts_map:
            raise ValueError(f"Неизвестный тип блока: {block_type}")
        
        return prompts_map[block_type]
    
    def _get_section_prompt(self, section_key: str) -> str:
        """Получить промпт для конкретного раздела платной версии"""
        
        section_methods = {
            "premium_analysis": PremiumPromptsNew.get_premium_analysis_prompt,
            "premium_strengths": PremiumPromptsNew.get_premium_strengths_prompt,
            "premium_growth_zones": PremiumPromptsNew.get_premium_growth_zones_prompt,
            "premium_compensation": PremiumPromptsNew.get_premium_compensation_prompt,
            "premium_interaction": PremiumPromptsNew.get_premium_interaction_prompt,
            "premium_prognosis": PremiumPromptsNew.get_premium_prognosis_prompt,
            "premium_practical": PremiumPromptsNew.get_premium_practical_prompt,
            "premium_conclusion": PremiumPromptsNew.get_premium_conclusion_prompt,
            "premium_appendix": PremiumPromptsNew.get_premium_appendix_prompt
        }
        
        if section_key not in section_methods:
            raise ValueError(f"Неизвестный раздел: {section_key}")
        
        return section_methods[section_key]()
    
    def _extract_page_count_from_description(self, description: str) -> float:
        """Извлекает количество страниц из описания подблока"""
        import re
        
        # Ищем паттерны типа "(1 страница)", "(1-2 страницы)", "(1,5 страницы)"
        patterns = [
            r'\((\d+(?:[,\.]\d+)?)\s*страниц?\w*\)',  # (1 страница), (1,5 страницы)
            r'\((\d+)-(\d+)\s*страниц?\w*\)',  # (1-2 страницы)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                if len(match.groups()) == 1:
                    # Простое число или дробь
                    page_str = match.group(1).replace(',', '.')
                    return float(page_str)
                elif len(match.groups()) == 2:
                    # Диапазон - берем среднее
                    start = float(match.group(1))
                    end = float(match.group(2))
                    return (start + end) / 2
        
        # По умолчанию 1 страница
        return 1.0
    
    def _get_premium_page_prompt(self, section_key: str, page_num: int, total_pages: int):
        """Получить КРАТКИЙ промпт для конкретной страницы премиум анализа (БЕЗ базового промпта)
        Возвращает: (промпт, ожидаемое_количество_страниц)"""
        
        # Карта описаний подблоков для каждого раздела  
        section_subblocks = {
            "premium_analysis": {
                "name": "Психологический портрет",
                "subblocks": [
                    "АНАЛИЗ BIG FIVE (1 страница)",
                    "ОПРЕДЕЛЕНИЕ ТИПА MBTI (1 страница)", 
                    "АРХЕТИПИЧЕСКАЯ СТРУКТУРА (1 страница)",
                    "КОГНИТИВНЫЙ ПРОФИЛЬ (1 страница)",
                    "ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ (1-2 страницы)",
                    "СИСТЕМА ЦЕННОСТЕЙ (1 страница)",
                    "КОММУНИКАТИВНЫЙ СТИЛЬ (1 страница)",
                    "МОТИВАЦИОННЫЕ ДРАЙВЕРЫ (1 страница)",
                    "ТЕНЕВЫЕ АСПЕКТЫ ЛИЧНОСТИ (1-2 страницы)",
                    "ЭКЗИСТЕНЦИАЛЬНАЯ ИСПОЛНЕННОСТЬ (1-2 страницы)"
                ]
            },
            "premium_strengths": {
                "name": "Сильные стороны и таланты",
                "subblocks": [
                    "ПРИРОДНЫЕ ТАЛАНТЫ (1,5 страницы)",
                    "ПРЕДРАСПОЛОЖЕННОСТИ К ОПРЕДЕЛЁННЫМ ОБЛАСТЯМ (0,5 страницы)",
                    "ПРИОБРЕТЁННЫЕ КОМПЕТЕНЦИИ (2 страницы)",
                    "РЕСУРСНЫЕ СОСТОЯНИЯ (2 страницы)",
                    "ПОТЕНЦИАЛ РАЗВИТИЯ (1 страница)",
                    "УНИКАЛЬНЫЕ КОМБИНАЦИИ КАЧЕСТВ (1 страница)"
                ]
            },
            "premium_growth_zones": {
                "name": "Зоны роста",
                "subblocks": [
                    "ОГРАНИЧИВАЮЩИЕ УБЕЖДЕНИЯ (1 страница)",
                    "ТРАНСФОРМАЦИЯ УБЕЖДЕНИЙ (0.5 страницы)",
                    "КОГНИТИВНЫЕ ИСКАЖЕНИЯ (1 страница)",
                    "СЛЕПЫЕ ЗОНЫ (1 страница)",
                    "ЭМОЦИОНАЛЬНЫЕ ТРИГГЕРЫ (2 страницы)",
                    "ПАТТЕРНЫ САМОСАБОТАЖА (1 страница)",
                    "СОМАТИЧЕСКИЕ ПРОЯВЛЕНИЯ (1 страница)"
                ]
            },
            "premium_compensation": {
                "name": "Компенсаторика",
                "subblocks": [
                    "СТРАТЕГИИ РАЗВИТИЯ (2 страницы)",
                    "ТЕХНИКИ САМОРЕГУЛЯЦИИ (1 страница)",
                    "АЛЬТЕРНАТИВНЫЕ МОДЕЛИ ПОВЕДЕНИЯ (1 страница)",
                    "РЕСУРСЫ ВОССТАНОВЛЕНИЯ (1 страница)",
                    "ИНДИВИДУАЛЬНЫЙ ПЛАН РАЗВИТИЯ (3 страницы)",
                    "РЕКОМЕНДУЕМЫЕ ПРАКТИКИ (2 страницы)",
                    "ОБРАЗНО-СИМВОЛИЧЕСКАЯ РАБОТА (1 страница)"
                ]
            },
            "premium_interaction": {
                "name": "Взаимодействие с окружающими",
                "subblocks": [
                    "СОВМЕСТИМОСТЬ (1 страница)",
                    "СТРАТЕГИИ ДЛЯ СЛОЖНЫХ СОЧЕТАНИЙ (1 страница)",
                    "ПЕРСОНАЛЬНЫЙ СТИЛЬ ОБЩЕНИЯ (1 страница)",
                    "ТЕХНИКИ АДАПТИВНОЙ КОММУНИКАЦИИ (1 страница)",
                    "РОЛЬ В КОМАНДЕ (1 страница)",
                    "БЛИЗКИЕ ОТНОШЕНИЯ (1 страница)",
                    "РАЗРЕШЕНИЕ КОНФЛИКТОВ (1 страница)",
                    "СЕМЕЙНЫЕ ПАТТЕРНЫ И ГРАНИЦЫ (1 страница)"
                ]
            },
            "premium_prognosis": {
                "name": "Прогностика",
                "subblocks": [
                    "ДВУХСЦЕНАРНЫЙ ПРОГНОЗ РАЗВИТИЯ (1 страница)",
                    "КРИЗИСЫ И ТОЧКИ РОСТА (1 страница)",
                    "САМОРЕАЛИЗАЦИЯ (1 страница)",
                    "ПРОГНОЗ РАЗВИТИЯ КАЧЕСТВ (1 страница)",
                    "ДОЛГОСРОЧНЫЕ ПЕРСПЕКТИВЫ (1 страница)"
                ]
            },
            "premium_practical": {
                "name": "Практическое приложение",
                "subblocks": [
                    "ПРОФРЕАЛИЗАЦИЯ (2 страницы)",
                    "ПРОДУКТИВНОСТЬ (2 страницы)",
                    "ПРИНЯТИЕ РЕШЕНИЙ (2 страницы)",
                    "СОЦИАЛЬНЫЕ НАВЫКИ (2 страницы)",
                    "ЗДОРОВЬЕ И БЛАГОПОЛУЧИЕ (2 страницы)",
                    "ТЕХНИКИ ДЛЯ СИЛЬНЫХ СТОРОН (1 страница)",
                    "УПРАЖНЕНИЯ ДЛЯ ЗОН РОСТА (1 страница)",
                    "ЧЕК-ЛИСТЫ И ТРЕКЕРЫ (1 страница)"
                ]
            },
            "premium_conclusion": {
                "name": "Заключение",
                "subblocks": [
                    "ОБОБЩЕНИЕ ИНСАЙТОВ (1 страница)",
                    "СИНТЕЗ СИЛЬНЫХ СТОРОН (1 страница)",
                    "МОТИВАЦИОННОЕ ПОСЛАНИЕ (1 страница)",
                    "РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ (1 страница)",
                    "ЭВОЛЮЦИЯ ЛИЧНОСТИ (1 страница)",
                    "ФИНАЛЬНОЕ ПОСЛАНИЕ (1 страница)"
                ]
            },
            "premium_appendix": {
                "name": "Приложения",
                "subblocks": [
                    "ГЛОССАРИЙ ТЕРМИНОВ (1 страница)",
                    "РЕКОМЕНДУЕМЫЕ РЕСУРСЫ (2 страницы)",
                    "ВИЗУАЛИЗАЦИИ И ДИАГРАММЫ (1 страница)",
                    "ПЕРСОНАЛЬНЫЕ АФФИРМАЦИИ (2 страницы)",
                    "ШАБЛОНЫ ДЛЯ САМОАНАЛИЗА (1 страница)",
                    "ПРОЕКТИВНЫЕ ОБРАЗЫ И МЕТАФОРЫ (1 страница)"
                ]
            }
        }
        
        if section_key not in section_subblocks:
            raise ValueError(f"Неизвестный раздел: {section_key}")
            
        if page_num > len(section_subblocks[section_key]["subblocks"]):
            raise ValueError(f"Неизвестная страница {page_num} в разделе {section_key}")
        
        section_name = section_subblocks[section_key]["name"]
        subblock_description = section_subblocks[section_key]["subblocks"][page_num - 1]
        
        # Извлекаем ожидаемый размер страницы
        expected_pages = self._extract_page_count_from_description(subblock_description)
        expected_chars = int(expected_pages * 3000)  # 3000 символов на страницу
        
        prompt = f"""Создайте СТРАНИЦУ {page_num} из {total_pages}.

🎯 СОДЕРЖАНИЕ:
{subblock_description}

🚨 ОБЪЁМ: ТОЧНО {expected_chars} символов (±100 максимум)

🎯 ТРЕБОВАНИЯ:
- Обращение через "ВЫ", "ВАШИ", "ВАМ"  
- Максимум 2-3 цитаты из ответов
- Финальный размер: {expected_chars} ± 100 символов

Используйте загруженные инструкции раздела."""

        return prompt, expected_pages

    def _create_section_prompt_with_markers(self, section_key: str, section_name: str, page_count: int, user_data: str) -> str:
        """Создает промпт для раздела с маркерами страниц"""
        
        # Получаем структуру страниц раздела
        section_structure = self._get_section_structure(section_key)
        
        # Формируем список страниц с маркерами
        pages_list = []
        for i, subblock in enumerate(section_structure, 1):
            pages_list.append(f"=== СТРАНИЦА {i} ===\n{subblock}")
        
        pages_text = "\n\n".join(pages_list)
        
        # Создаем сжатый профиль пользователя для экономии токенов
        compressed_profile = self._create_compressed_user_profile(user_data)
        
        prompt = f"""Создайте ПОЛНЫЙ раздел "{section_name}" ({page_count} страниц).

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
{compressed_profile}

ИНСТРУКЦИИ РАЗДЕЛА:
{self._get_section_prompt(section_key)}

СТРУКТУРА СТРАНИЦ:
{pages_text}

ТРЕБОВАНИЯ:
- Каждая страница должна быть ~3000 символов
- Используйте маркеры === СТРАНИЦА X === для разделения
- Обращение через "ВЫ", "ВАШИ", "ВАМ"
- Максимум 2-3 цитаты из ответов на страницу
- Создайте {page_count} страниц согласно структуре

Начните с маркера === СТРАНИЦА 1 === и создайте все страницы раздела."""

        return prompt

    def _create_compressed_user_profile(self, user_data: str) -> str:
        """Создает сжатый профиль пользователя для экономии токенов"""
        
        # Простое извлечение ключевых характеристик
        characteristics = []
        
        if "одиночестве" in user_data.lower() or "сам" in user_data.lower():
            characteristics.append("интроверт")
        if "люди" in user_data.lower() or "команда" in user_data.lower():
            characteristics.append("социальный")
        if "анализ" in user_data.lower() or "логика" in user_data.lower():
            characteristics.append("аналитик")
        if "чувства" in user_data.lower() or "эмоции" in user_data.lower():
            characteristics.append("эмпат")
        if "план" in user_data.lower() or "структура" in user_data.lower():
            characteristics.append("организованный")
        if "совершенство" in user_data.lower() or "качество" in user_data.lower():
            characteristics.append("перфекционист")
        if "творчество" in user_data.lower() or "нестандартные" in user_data.lower():
            characteristics.append("креативный")
        if "стабильность" in user_data.lower() or "предсказуемость" in user_data.lower():
            characteristics.append("стабильный")
        if "ответственность" in user_data.lower() or "обязательства" in user_data.lower():
            characteristics.append("ответственный")
        if "развитие" in user_data.lower() or "рост" in user_data.lower():
            characteristics.append("развивающийся")
        
        if characteristics:
            return f"Ключевые характеристики: {', '.join(characteristics[:5])}"
        else:
            return "Профиль: смешанный тип личности с разнообразными качествами"

    def _get_section_structure(self, section_key: str) -> List[str]:
        """Получает структуру страниц для раздела"""
        
        section_subblocks = {
            "premium_analysis": [
                "АНАЛИЗ BIG FIVE (1 страница)",
                "ОПРЕДЕЛЕНИЕ ТИПА MBTI (1 страница)", 
                "АРХЕТИПИЧЕСКАЯ СТРУКТУРА (1 страница)",
                "КОГНИТИВНЫЙ ПРОФИЛЬ (1 страница)",
                "ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ (1-2 страницы)",
                "СИСТЕМА ЦЕННОСТЕЙ (1 страница)",
                "КОММУНИКАТИВНЫЙ СТИЛЬ (1 страница)",
                "МОТИВАЦИОННЫЕ ДРАЙВЕРЫ (1 страница)",
                "ТЕНЕВЫЕ АСПЕКТЫ ЛИЧНОСТИ (1-2 страницы)",
                "ЭКЗИСТЕНЦИАЛЬНАЯ ИСПОЛНЕННОСТЬ (1-2 страницы)"
            ],
            "premium_strengths": [
                "ПРИРОДНЫЕ ТАЛАНТЫ (1,5 страницы)",
                "ПРИОБРЕТЁННЫЕ КОМПЕТЕНЦИИ (2 страницы)",
                "РЕСУРСНЫЕ СОСТОЯНИЯ (2 страницы)",
                "ПОТЕНЦИАЛ РАЗВИТИЯ (1 страница)",
                "УНИКАЛЬНЫЕ КОМБИНАЦИИ КАЧЕСТВ (1 страница)"
            ],
            "premium_growth_zones": [
                "ОГРАНИЧИВАЮЩИЕ УБЕЖДЕНИЯ (1 страница)",
                "ТРАНСФОРМАЦИЯ УБЕЖДЕНИЙ (0.5 страницы)",
                "КОГНИТИВНЫЕ ИСКАЖЕНИЯ (1 страница)",
                "СЛЕПЫЕ ЗОНЫ (1 страница)",
                "ЭМОЦИОНАЛЬНЫЕ ТРИГГЕРЫ (2 страницы)",
                "ПАТТЕРНЫ САМОСАБОТАЖА (1 страница)",
                "СОМАТИЧЕСКИЕ ПРОЯВЛЕНИЯ (1 страница)"
            ],
            "premium_compensation": [
                "СТРАТЕГИИ РАЗВИТИЯ (2 страницы)",
                "ТЕХНИКИ САМОРЕГУЛЯЦИИ (1 страница)",
                "АЛЬТЕРНАТИВНЫЕ МОДЕЛИ ПОВЕДЕНИЯ (1 страница)",
                "РЕСУРСЫ ВОССТАНОВЛЕНИЯ (1 страница)",
                "ИНДИВИДУАЛЬНЫЙ ПЛАН РАЗВИТИЯ (3 страницы)",
                "РЕКОМЕНДУЕМЫЕ ПРАКТИКИ (2 страницы)",
                "ОБРАЗНО-СИМВОЛИЧЕСКАЯ РАБОТА (1 страница)"
            ],
            "premium_interaction": [
                "СОВМЕСТИМОСТЬ (1 страница)",
                "СТРАТЕГИИ ДЛЯ СЛОЖНЫХ СОЧЕТАНИЙ (1 страница)",
                "ПЕРСОНАЛЬНЫЙ СТИЛЬ ОБЩЕНИЯ (1 страница)",
                "ТЕХНИКИ АДАПТИВНОЙ КОММУНИКАЦИИ (1 страница)",
                "РОЛЬ В КОМАНДЕ (1 страница)",
                "БЛИЗКИЕ ОТНОШЕНИЯ (1 страница)",
                "РАЗРЕШЕНИЕ КОНФЛИКТОВ (1 страница)",
                "СЕМЕЙНЫЕ ПАТТЕРНЫ И ГРАНИЦЫ (1 страница)"
            ],
            "premium_prognosis": [
                "ДВУХСЦЕНАРНЫЙ ПРОГНОЗ РАЗВИТИЯ (1 страница)",
                "КРИЗИСЫ И ТОЧКИ РОСТА (1 страница)",
                "САМОРЕАЛИЗАЦИЯ (1 страница)",
                "ПРОГНОЗ РАЗВИТИЯ КАЧЕСТВ (1 страница)",
                "ДОЛГОСРОЧНЫЕ ПЕРСПЕКТИВЫ (1 страница)"
            ],
            "premium_practical": [
                "ПРОФРЕАЛИЗАЦИЯ (2 страницы)",
                "ПРОДУКТИВНОСТЬ (2 страницы)",
                "ПРИНЯТИЕ РЕШЕНИЙ (2 страницы)",
                "СОЦИАЛЬНЫЕ НАВЫКИ (2 страницы)",
                "ЗДОРОВЬЕ И БЛАГОПОЛУЧИЕ (2 страницы)",
                "ТЕХНИКИ ДЛЯ СИЛЬНЫХ СТОРОН (1 страница)",
                "УПРАЖНЕНИЯ ДЛЯ ЗОН РОСТА (1 страница)",
                "ЧЕК-ЛИСТЫ И ТРЕКЕРЫ (1 страница)"
            ],
            "premium_conclusion": [
                "ОБОБЩЕНИЕ ИНСАЙТОВ (1 страница)",
                "СИНТЕЗ СИЛЬНЫХ СТОРОН (1 страница)",
                "МОТИВАЦИОННОЕ ПОСЛАНИЕ (1 страница)",
                "РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ (1 страница)",
                "ЭВОЛЮЦИЯ ЛИЧНОСТИ (1 страница)",
                "ФИНАЛЬНОЕ ПОСЛАНИЕ (1 страница)"
            ],
            "premium_appendix": [
                "ГЛОССАРИЙ ТЕРМИНОВ (1 страница)",
                "РЕКОМЕНДУЕМЫЕ РЕСУРСЫ (2 страницы)",
                "ВИЗУАЛИЗАЦИИ И ДИАГРАММЫ (1 страница)",
                "ПЕРСОНАЛЬНЫЕ АФФИРМАЦИИ (2 страницы)",
                "ШАБЛОНЫ ДЛЯ САМОАНАЛИЗА (1 страница)",
                "ПРОЕКТИВНЫЕ ОБРАЗЫ И МЕТАФОРЫ (1 страница)"
            ]
        }
        
        return section_subblocks.get(section_key, [])

    def _parse_section_response(self, response_content: str, section_key: str, section_name: str, page_count: int, start_page: int) -> Dict[str, str]:
        """Парсит ответ ИИ на отдельные страницы по маркерам"""
        
        pages = {}
        
        # Проверяем общий размер ответа
        total_content_length = len(response_content.strip())
        min_expected_length = page_count * 200  # Минимум 200 символов на страницу
        
        if total_content_length < min_expected_length:
            error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: ИИ вернул слишком короткий ответ для раздела '{section_name}'. Получено {total_content_length} символов, ожидалось минимум {min_expected_length} символов. Это указывает на ошибку в генерации ответа."
            print(error_msg)
            raise ValueError(error_msg)
        
        # Разделяем по маркерам === СТРАНИЦА X ===
        import re
        page_pattern = r'=== СТРАНИЦА (\d+) ===\s*(.*?)(?=\s*=== СТРАНИЦА \d+ ===|$)'
        matches = re.findall(page_pattern, response_content, re.DOTALL)
        
        if matches:
            # Обрабатываем найденные страницы
            for page_num_str, page_content in matches:
                page_num = int(page_num_str)
                global_page = start_page + page_num - 1
                
                # Очищаем контент от лишних пробелов
                clean_content = page_content.strip()
                
                # Проверяем размер каждой страницы
                if len(clean_content) < 200:
                    error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: Страница {global_page} слишком короткая ({len(clean_content)} символов). Ожидалось минимум 200 символов. Это указывает на ошибку в генерации ответа."
                    print(error_msg)
                    raise ValueError(error_msg)
                
                if clean_content:
                    page_key = f"page_{global_page:02d}"
                    pages[page_key] = {
                        "content": clean_content,
                        "section": section_name,
                        "section_key": section_key,
                        "page_num": page_num,
                        "global_page": global_page
                    }
                    
                    print(f"   📄 Страница {global_page}: {len(clean_content)} символов")
        else:
            # Если маркеры не найдены, делим контент на равные части
            print(f"⚠️ Маркеры страниц не найдены, делим контент на {page_count} частей")
            content_length = len(response_content)
            part_length = content_length // page_count
            
            for i in range(page_count):
                start_pos = i * part_length
                end_pos = start_pos + part_length if i < page_count - 1 else content_length
                
                page_content = response_content[start_pos:end_pos].strip()
                global_page = start_page + i
                
                # Проверяем размер каждой страницы
                if len(page_content) < 200:
                    error_msg = f"❌ КРИТИЧЕСКАЯ ОШИБКА: Страница {global_page} слишком короткая ({len(page_content)} символов). Ожидалось минимум 200 символов. Это указывает на ошибку в генерации ответа."
                    print(error_msg)
                    raise ValueError(error_msg)
                
                page_key = f"page_{global_page:02d}"
                pages[page_key] = {
                    "content": page_content,
                    "section": section_name,
                    "section_key": section_key,
                    "page_num": i + 1,
                    "global_page": global_page
                }
                
                print(f"   📄 Страница {global_page}: {len(page_content)} символов")
        
        return pages

    def _estimate_token_count(self, text: str) -> int:
        """Приблизительная оценка количества токенов в тексте (примерно 4 символа = 1 токен для русского)"""
        return len(text) // 3  # Более консервативная оценка для русского текста
    
    def _estimate_conversation_tokens(self, conversation: List[Dict]) -> int:
        """Оценка общего количества токенов в разговоре"""
        total_chars = 0
        for message in conversation:
            total_chars += len(message.get("content", ""))
        return total_chars // 3  # Прямой подсчет: ~3 символа = 1 токен для русского
    
    def _trim_conversation_context(self, conversation: List[Dict], max_tokens: int = 30000) -> List[Dict]:
        """Урезание контекста беседы по лимиту токенов"""
        
        current_tokens = self._estimate_conversation_tokens(conversation)
        
        if current_tokens <= max_tokens:
            return conversation
            
        # Всегда сохраняем системный промпт + данные пользователя + первичный анализ
        if len(conversation) <= 3:
            return conversation
            
        preserved_messages = conversation[:3]
        remaining_messages = conversation[3:]
        
        # Группируем в пары (user запрос + assistant ответ)
        pairs = []
        for i in range(0, len(remaining_messages), 2):
            if i + 1 < len(remaining_messages):
                pair = [remaining_messages[i], remaining_messages[i + 1]]
                pair_tokens = self._estimate_token_count(pair[0].get("content", "") + pair[1].get("content", ""))
                pairs.append((pair, pair_tokens))
        
        # Берем последние пары, пока не превысим лимит
        kept_pairs = []
        current_size = self._estimate_conversation_tokens(preserved_messages)
        
        for pair, pair_tokens in reversed(pairs):
            if current_size + pair_tokens <= max_tokens:
                kept_pairs.insert(0, pair)
                current_size += pair_tokens
            else:
                break
        
        # Собираем обратно
        trimmed_conversation = preserved_messages[:]
        for pair in kept_pairs:
            trimmed_conversation.extend(pair)
        
        final_tokens = self._estimate_conversation_tokens(trimmed_conversation)
        print(f"🔄 Урезали контекст: {current_tokens} → {final_tokens} токенов (сохранено {len(kept_pairs)} страниц)")
        
        return trimmed_conversation


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
        print(f"⚠️ ВНИМАНИЕ: Используется fallback анализ")

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

    async def generate_premium_report(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Генерация платного психологического отчета (50 вопросов) - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ"""

        try:
            if not self.perplexity_enabled or not self.ai_service:
                print(f"❌ Perplexity AI отключен - невозможно создать премиум отчет")
                return {
                    "success": False,
                    "error": "Perplexity AI отключен. Проверьте настройки API.",
                    "stage": "initialization"
                }

            # 🧠 ОПТИМИЗИРОВАННЫЙ платный анализ: 9 запросов вместо 74
            print(f"🧠 Запускаем ОПТИМИЗИРОВАННЫЙ ПЛАТНЫЙ AI анализ для пользователя {user.telegram_id}...")
            analysis_result = await self.ai_service.analyze_premium_responses_optimized(user, questions, answers)

            if not analysis_result.get("success"):
                error_msg = analysis_result.get("error", "Неизвестная ошибка API")
                print(f"❌ Оптимизированный платный AI анализ неудачен: {error_msg}")
                
                # Проверяем, является ли это ошибкой валидации (короткий ответ)
                if "короткий" in error_msg.lower() or "короткая" in error_msg.lower():
                    return {
                        "success": False,
                        "error": f"Критическая ошибка: ИИ не смог сгенерировать полноценный ответ. {error_msg}",
                        "stage": "ai_validation"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Ошибка API при генерации анализа: {error_msg}",
                        "stage": "ai_analysis"
                    }

            # Создаем PDF отчет (платная версия)
            print(f"📄 Создаем ПЛАТНЫЙ PDF отчет...")
            report_filepath = self.report_generator.create_premium_pdf_report(user, analysis_result)

            print(f"✅ Платный отчет успешно создан: {report_filepath}")

            return {
                "success": True,
                "premium_analysis": analysis_result["premium_analysis"],
                "premium_strengths": analysis_result["premium_strengths"],
                "premium_growth_zones": analysis_result["premium_growth_zones"],
                "premium_compensation": analysis_result["premium_compensation"],
                "premium_interaction": analysis_result["premium_interaction"],
                "premium_prognosis": analysis_result["premium_prognosis"],
                "premium_practical": analysis_result["premium_practical"],
                "premium_conclusion": analysis_result["premium_conclusion"],
                "premium_appendix": analysis_result["premium_appendix"],
                "report_file": report_filepath,
                "usage": analysis_result.get("usage", {}),
                "character_stats": analysis_result.get("character_stats", {}),
                "timestamp": analysis_result["timestamp"]
            }

        except Exception as e:
            print(f"❌ Ошибка при генерации платного отчета: {e}")
            return {
                "success": False,
                "error": str(e),
                "stage": "premium"
            }


