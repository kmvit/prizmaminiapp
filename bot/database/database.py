from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from bot.config import DATABASE_URL
from bot.database.models import Base
from sqlalchemy import text # Добавляем импорт text

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Включаем логирование SQL-запросов
    poolclass=NullPool  # Отключаем пул соединений для SQLite
)

# Создаем фабрику сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Получение сессии базы данных"""
    async with async_session() as session:
        yield session

async def add_premium_paid_column():
    """Добавляет столбец is_premium_paid в таблицу users, если он еще не существует."""
    async with engine.begin() as conn:
        # Проверяем, существует ли столбец перед добавлением
        # Это предотвратит ошибку, если функция будет вызвана повторно
        result = await conn.execute(text("PRAGMA table_info(users);"))
        columns = [row[1] for row in result.fetchall()]
        
        if "is_premium_paid" not in columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_premium_paid BOOLEAN DEFAULT FALSE;"))
            print("✅ Столбец 'is_premium_paid' успешно добавлен в таблицу 'users'.")
        else:
            print("ℹ️ Столбец 'is_premium_paid' уже существует в таблице 'users'. Пропуск операции.") 