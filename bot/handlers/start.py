"""
Обработчик команды /start
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.services.telegram_service import telegram_service
from bot.services.database_service import db_service
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    chat_id = message.chat.id
    
    try:
        logger.info(f"🚀 Получена команда /start от пользователя {chat_id}")
        
        # Создаем или получаем пользователя в базе данных
        user = await db_service.get_or_create_user(telegram_id=chat_id)
        logger.info(f"👤 Пользователь создан/получен: id={user.id}, telegram_id={chat_id}")
        
        # Отправляем приветственное сообщение
        success = await telegram_service.send_start_message(chat_id)
        
        if success:
            logger.info(f"✅ Приветственное сообщение отправлено пользователю {chat_id}")
        else:
            logger.error(f"❌ Не удалось отправить приветственное сообщение пользователю {chat_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке команды /start для пользователя {chat_id}: {e}")
        # Пытаемся отправить сообщение об ошибке пользователю
        try:
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        except:
            pass

