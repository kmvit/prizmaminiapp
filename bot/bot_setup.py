"""
Настройка и инициализация Telegram бота через aiogram
"""
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from bot.handlers import start
from bot.utils.logger import get_logger

logger = get_logger(__name__)

# Инициализация бота и диспетчера
bot_token = os.getenv("BOT_TOKEN")
bot = None
dp = None

if bot_token:
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(start.router)
    
    logger.info("✅ Aiogram бот инициализирован")
else:
    logger.warning("⚠️ BOT_TOKEN не настроен, aiogram бот не инициализирован")


async def process_update(update_dict: dict) -> bool:
    """
    Обработать обновление от Telegram через aiogram dispatcher
    
    Args:
        update_dict: Словарь с данными обновления от Telegram
        
    Returns:
        True если обработка прошла успешно
    """
    if not bot or not dp:
        logger.warning("⚠️ Бот не инициализирован, обновление не обработано")
        return False
    
    try:
        logger.info(f"🔄 [bot_setup] Обработка обновления через aiogram")
        
        # Создаем объект Update из словаря
        # В aiogram 3.x нужно использовать model_validate для создания объектов из JSON
        try:
            update = Update.model_validate(update_dict)
            logger.info(f"✅ [bot_setup] Update объект создан через model_validate")
        except Exception as parse_error:
            # Fallback: пытаемся создать через конструктор
            logger.warning(f"⚠️ [bot_setup] Ошибка при парсинге Update через model_validate: {parse_error}")
            try:
                update = Update(**update_dict)
                logger.info(f"✅ [bot_setup] Update объект создан через конструктор")
            except Exception as constr_error:
                logger.error(f"❌ [bot_setup] Ошибка при создании Update через конструктор: {constr_error}")
                raise
        
        # Обрабатываем обновление через диспетчер
        # В aiogram 3.x используем feed_update с bot и update
        logger.info(f"🔄 [bot_setup] Передаем обновление в диспетчер...")
        await dp.feed_update(bot, update)
        
        logger.info(f"✅ [bot_setup] Обновление обработано диспетчером")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке обновления через aiogram: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return False


async def close_bot():
    """Закрыть сессию бота"""
    if bot:
        await bot.session.close()
        logger.info("✅ Сессия бота закрыта")

