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

    async def analyze_text(self, text: str) -> dict:
        """
        Анализирует текст с помощью Perplexity API
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "mixtral-8x7b-instruct",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты - психолог, который анализирует тексты и дает профессиональные рекомендации."
                            },
                            {
                                "role": "user",
                                "content": text
                            }
                        ]
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Perplexity API error: {error_text}")
                        raise Exception(f"Perplexity API error: {response.status}")

        except Exception as e:
            logger.error(f"Error in Perplexity API call: {str(e)}")
            raise

# Создаем экземпляр сервиса
perplexity_service = PerplexityService() 