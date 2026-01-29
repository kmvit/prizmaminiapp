#!/usr/bin/env python3
"""
Скрипт для очистки базы данных
Удаляет все данные, но сохраняет структуру таблиц
"""

import asyncio
from sqlalchemy import delete, text
from bot.database.database import async_session, engine
from bot.database.models import User, Answer, Payment, Question
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
            
            logger.info(f"📊 Найдено записей: пользователей={users_count}, ответов={answers_count}, платежей={payments_count}")
            
            # Удаляем все данные
            await session.execute(delete(Answer))
            logger.info("✅ Удалены все ответы")
            
            await session.execute(delete(Payment))
            logger.info("✅ Удалены все платежи")
            
            # Для пользователей сбрасываем данные, но не удаляем (чтобы сохранить структуру)
            await session.execute(
                text("""
                    UPDATE users SET
                        is_paid = 0,
                        is_premium_paid = 0,
                        test_completed = 0,
                        current_question_id = NULL,
                        test_started_at = NULL,
                        test_completed_at = NULL,
                        free_report_status = 'PENDING',
                        premium_report_status = 'PENDING',
                        free_report_path = NULL,
                        premium_report_path = NULL,
                        report_generation_error = NULL,
                        report_generation_started_at = NULL,
                        report_generation_completed_at = NULL,
                        special_offer_started_at = NULL,
                        notification_6_hours_sent = 0,
                        notification_1_hour_sent = 0,
                        notification_10_minutes_sent = 0,
                        updated_at = CURRENT_TIMESTAMP
                """)
            )
            logger.info("✅ Сброшены все данные пользователей")
            
            # Удаляем пользователей (если нужно полностью очистить)
            # await session.execute(delete(User))
            # logger.info("✅ Удалены все пользователи")
            
            await session.commit()
            logger.info("✅ Все изменения сохранены")
            
            # Проверяем результат
            users_count_after = await session.scalar(select(func.count()).select_from(User))
            answers_count_after = await session.scalar(select(func.count()).select_from(Answer))
            payments_count_after = await session.scalar(select(func.count()).select_from(Payment))
            
            logger.info(f"📊 После очистки: пользователей={users_count_after}, ответов={answers_count_after}, платежей={payments_count_after}")
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
