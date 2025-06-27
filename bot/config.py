import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Загружаем переменные окружения из .env файла с перезаписью системных переменных
load_dotenv(override=True)

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

# Конфигурация базы данных
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATABASE_DIR}/bot.db")

# Telegram Bot (для Mini App - не обязательно)
# BOT_TOKEN = os.getenv("BOT_TOKEN")

# Perplexity API
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online")
PERPLEXITY_ENABLED = os.getenv("PERPLEXITY_ENABLED", "false").lower() == "true"

# Robokassa
ROBOKASSA_LOGIN = os.getenv("ROBOKASSA_LOGIN")
ROBOKASSA_PASSWORD = os.getenv("ROBOKASSA_PASSWORD")
ROBOKASSA_PASSWORD2 = os.getenv("ROBOKASSA_PASSWORD2")
ROBOKASSA_TEST = os.getenv("ROBOKASSA_TEST", "1") == "1"

# Настройки тестирования
FREE_QUESTIONS_LIMIT = int(os.getenv("FREE_QUESTIONS_LIMIT", "10"))  # Количество бесплатных вопросов

class Settings(BaseSettings):
    # BOT_TOKEN: str  # Не нужен для веб-приложения
    WEBAPP_URL: str = "http://localhost:8080"
    DATABASE_URL: str
    PERPLEXITY_API_KEY: str = ""  # Делаем необязательным
    PERPLEXITY_MODEL: str = "llama-3.1-sonar-small-128k-online"  # Модель по умолчанию
    PERPLEXITY_ENABLED: bool = False  # По умолчанию отключено
    ROBOKASSA_LOGIN: str
    ROBOKASSA_PASSWORD: str
    ROBOKASSA_PASSWORD2: str = "default_password2"
    ROBOKASSA_TEST: str = "1"
    FREE_QUESTIONS_LIMIT: int = 10  # Количество бесплатных вопросов

    class Config:
        env_file = ".env"
        extra = "ignore"  # Игнорировать дополнительные поля

# Создаем настройки (Perplexity необязателен)
try:
    settings = Settings()
    if not PERPLEXITY_ENABLED:
        print("ℹ️ Perplexity API отключен")
    else:
        print("✅ Perplexity API включен")
except Exception as e:
    print(f"⚠️ Не удалось загрузить настройки из pydantic: {e}")
    settings = None