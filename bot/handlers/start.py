"""
Обработчик команды /start
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.database_service import db_service
from bot.utils.logger import get_logger
import os

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
        
        # Формируем приветственное сообщение
        welcome_text = """
👋 <b>Добро пожаловать в PRIZMA!</b>

Ваш личный ИИ психолог и наставник поможет вам:

🧠 Расшифровать вашу личность на 100%
📊 Получить глубокий психологический анализ
💡 Узнать свои сильные стороны и зоны роста
🚀 Получить персональный план развития

Начните свой путь к самопознанию прямо сейчас!
        """.strip()
        
        # Создаем кнопку для открытия Web App
        webapp_url = os.getenv("WEBAPP_URL", "")
        if webapp_url:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🚀 Начать тест",
                    web_app={"url": f"{webapp_url.rstrip('/')}/index.html"}
                )
            ]])
        else:
            keyboard = None
        
        # Отправляем сообщение через aiogram
        await message.answer(
            welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Приветственное сообщение отправлено пользователю {chat_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке команды /start для пользователя {chat_id}: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        # Пытаемся отправить сообщение об ошибке пользователю
        try:
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        except:
            pass


@router.message(Command("test_browser"))
async def cmd_test_browser(message: Message):
    """Тестовая команда для проверки открытия ссылки в системном браузере"""
    chat_id = message.chat.id
    
    try:
        logger.info(f"🧪 Получена команда /test_browser от пользователя {chat_id}")
        
        # Создаем сообщение с кнопкой на yandex.ru
        test_text = """
🧪 <b>Тест открытия ссылки</b>

Нажмите кнопку ниже, чтобы проверить, через какой браузер откроется ссылка.

Если откроется в системном браузере (Safari/Chrome) - значит работает правильно ✅
Если откроется в Telegram браузере - значит нужно использовать другой подход ❌
        """.strip()
        
        # Создаем кнопку с url (должна открыться в системном браузере)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🔗 Открыть Yandex.ru",
                url="https://yandex.ru"
            )
        ]])
        
        # Отправляем сообщение
        await message.answer(
            test_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Тестовое сообщение отправлено пользователю {chat_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке команды /test_browser для пользователя {chat_id}: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        try:
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        except:
            pass

