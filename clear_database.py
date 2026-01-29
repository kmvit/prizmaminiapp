#!/usr/bin/env python3
"""
Скрипт для очистки базы данных
Удаляет все данные, но сохраняет структуру таблиц
"""

import asyncio
from sqlalchemy import delete, text
from bot.database.database import async_session, engine
from bot.database.models import User, Answer, Payment, Question, Report
from loguru import logger

async def clear_database():
    """Очистка всех данных из базы данных"""
    try:
        logger.info("🧹 Начинаем очистку базы данных...")
        
        async with async_session() as session:
            # Получаем количество записей перед удалением
            from sqlalchemy import select, func
            
            users_count = await session.scalar(select(func.count()).select_from(User))
            answers_count = await session.scalar(select(func.count()).select_from(Answer))
            payments_count = await session.scalar(select(func.count()).select_from(Payment))
            reports_count = await session.scalar(select(func.count()).select_from(Report))
            
            logger.info(f"📊 Найдено записей: пользователей={users_count}, ответов={answers_count}, платежей={payments_count}, отчетов={reports_count}")
            
            # Удаляем все данные в правильном порядке (сначала зависимые таблицы)
            await session.execute(delete(Answer))
            logger.info("✅ Удалены все ответы")
            
            await session.execute(delete(Payment))
            logger.info("✅ Удалены все платежи")
            
            await session.execute(delete(Report))
            logger.info("✅ Удалены все отчеты")
            
            # Удаляем пользователей (это также удалит все связанные данные благодаря каскадному удалению)
            await session.execute(delete(User))
            logger.info("✅ Удалены все пользователи")
            
            await session.commit()
            logger.info("✅ Все изменения сохранены")
            
            # Проверяем результат
            users_count_after = await session.scalar(select(func.count()).select_from(User))
            answers_count_after = await session.scalar(select(func.count()).select_from(Answer))
            payments_count_after = await session.scalar(select(func.count()).select_from(Payment))
            reports_count_after = await session.scalar(select(func.count()).select_from(Report))
            
            logger.info(f"📊 После очистки: пользователей={users_count_after}, ответов={answers_count_after}, платежей={payments_count_after}, отчетов={reports_count_after}")
            logger.info("🎉 База данных успешно очищена!")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке базы данных: {e}")
        raise

async def main():
    """Главная функция"""
    try:
        await clear_database()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
