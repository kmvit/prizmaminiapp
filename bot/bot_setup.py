"""
Настройка и инициализация Telegram бота через aiogram
Использует polling для получения обновлений (не требует webhook)
"""
import os
from aiogram import Bot, Dispatcher
from bot.handlers import start, admin
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
    dp.include_router(admin.router)
    
    logger.info("✅ Aiogram бот инициализирован")
else:
    logger.warning("⚠️ BOT_TOKEN не настроен, aiogram бот не инициализирован")


async def start_polling():
    """Запустить polling для получения обновлений от Telegram"""
    if not bot or not dp:
        logger.warning("⚠️ Бот не инициализирован, polling не запущен")
        return
    
    try:
        logger.info("🔄 Запуск polling для получения обновлений от Telegram...")
        # Удаляем webhook если он был настроен (чтобы использовать polling)
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Старый webhook удален")
        except Exception as e:
            logger.debug(f"ℹ️ Webhook не был настроен или ошибка при удалении: {e}")
        
        # Запускаем polling
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске polling: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")


async def stop_polling():
    """Остановить polling"""
    if dp:
        try:
            await dp.stop_polling()
            logger.info("✅ Polling остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке polling: {e}")


async def close_bot():
    """Закрыть сессию бота"""
    if bot:
        await bot.session.close()
        logger.info("✅ Сессия бота закрыта")

