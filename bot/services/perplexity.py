import aiohttp
from bot.config import PERPLEXITY_API_KEY
from loguru import logger

class PerplexityService:
    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Список моделей в порядке приоритета (fallback)
        self.models = [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online", 
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct"
        ]

    async def analyze_text(self, text: str) -> dict:
        """
        Анализирует текст с помощью Perplexity API с fallback моделями
        """
        last_error = None
        
        for i, model in enumerate(self.models):
            try:
                logger.info(f"🤖 Пробуем модель {model} (попытка {i+1}/{len(self.models)})")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json={
                            "model": model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "Ты - психолог, который анализирует тексты и дает профессиональные рекомендации. Дай краткий психологический анализ ответа на вопрос."
                                },
                                {
                                    "role": "user", 
                                    "content": f"Проанализируй этот ответ на психологический вопрос: {text[:1000]}"  # Ограничиваем длину
                                }
                            ],
                            "max_tokens": 500,  # Ограничиваем размер ответа
                            "temperature": 0.7
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"✅ Успешно использована модель {model}")
                            return result
                        else:
                            error_text = await response.text()
                            error_msg = f"Perplexity API error with model {model}: {error_text}"
                            logger.warning(error_msg)
                            last_error = Exception(error_msg)
                            
                            # Если ошибка 400 (Invalid model), пробуем следующую модель
                            if response.status == 400:
                                continue
                            else:
                                # Для других ошибок (rate limit, auth etc) прерываем
                                raise Exception(f"Perplexity API error: {response.status}")

            except Exception as e:
                logger.warning(f"⚠️ Ошибка с моделью {model}: {str(e)}")
                last_error = e
                continue
        
        # Если все модели не сработали
        logger.error(f"❌ Все модели Perplexity API не сработали. Последняя ошибка: {last_error}")
        
        # Возвращаем fallback ответ вместо исключения
        return {
            "choices": [{
                "message": {
                    "content": "Анализ временно недоступен. Ваш ответ сохранен и будет проанализирован позже."
                }
            }]
        }

# Создаем экземпляр сервиса
perplexity_service = PerplexityService() 