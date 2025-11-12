"""
Сервис для работы с Telegram Bot API
Отправка сообщений и файлов пользователям
"""

import os
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any
from bot.config import settings
from bot.utils.logger import get_logger
import json

logger = get_logger(__name__)

class TelegramService:
    """Сервис для отправки сообщений в Telegram бота"""
    
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        # URL веб-приложения (для формирования абсолютных ссылок на скачивание)
        self.webapp_url = getattr(settings, "WEBAPP_URL", "").rstrip("/") if settings else ""
        # Безопасный лимит размера файла (МБ) для отправки через Bot API
        self.max_document_mb = int(os.getenv("TELEGRAM_MAX_DOCUMENT_MB", "45"))
        
        if not self.bot_token:
            logger.warning("⚠️ BOT_TOKEN не настроен, отправка в Telegram отключена")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ Telegram сервис инициализирован")
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        """Отправить текстовое сообщение"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, сообщение не отправлено")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info(f"✅ Сообщение отправлено пользователю {chat_id}")
                            return True
                        else:
                            logger.error(f"❌ Ошибка отправки сообщения: {result}")
                            return False
                    else:
                        logger.error(f"❌ HTTP ошибка при отправке сообщения: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке сообщения пользователю {chat_id}: {e}")
            return False
    
    async def send_document(self, chat_id: int, file_path: str, caption: str = "") -> bool:
        """Отправить документ (файл)"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, документ не отправлен")
            return False
            
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ Файл не найден: {file_path}")
                return False
                
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendDocument"
                
                with open(file_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('chat_id', str(chat_id))
                    data.add_field('document', file, filename=os.path.basename(file_path))
                    if caption:
                        data.add_field('caption', caption)
                    
                    async with session.post(url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("ok"):
                                logger.info(f"✅ Документ отправлен пользователю {chat_id}: {os.path.basename(file_path)}")
                                return True
                            else:
                                logger.error(f"❌ Ошибка отправки документа: {result}")
                                return False
                        else:
                            logger.error(f"❌ HTTP ошибка при отправке документа: {response.status}")
                            return False
                            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке документа пользователю {chat_id}: {e}")
            return False
    
    async def send_report_ready_notification(self, telegram_id: int, report_path: str, is_premium: bool = False) -> bool:
        """Отправить уведомление о готовности отчета"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, уведомление не отправлено")
            return False
            
        try:
            # Формируем сообщение
            report_type = "премиум" if is_premium else "бесплатный"
            message = f"""
🎉 Ваш {report_type} отчет готов!

📄 Мы проанализировали ваши ответы и создали персональный психологический портрет.

📎 Отчет прикреплен к этому сообщению.

💡 Вы также можете скачать отчет в веб-приложении
            """.strip()
            # Если файл слишком большой для отправки документом — отправляем ссылку вместо файла
            try:
                file_size_mb = round(os.path.getsize(report_path) / (1024 * 1024), 2)
            except Exception:
                file_size_mb = 0

            download_url = self._build_download_url(telegram_id, is_premium)

            if file_size_mb >= self.max_document_mb or not download_url:
                if file_size_mb >= self.max_document_mb:
                    logger.warning(f"⚠️ Файл слишком большой для отправки через бота ({file_size_mb} МБ ≥ {self.max_document_mb} МБ). Отправляем ссылку.")
                # Отправляем ссылку на скачивание
                link_message = self._compose_link_message(is_premium, download_url)
                success = await self.send_message(telegram_id, link_message)
                
                # Если это бесплатный отчет, отправляем предложение премиум-отчета
                if success and not is_premium:
                    await self.send_premium_offer(telegram_id)
                
                return success
            
            # Отправляем сообщение с файлом
            success = await self.send_document(
                chat_id=telegram_id,
                file_path=report_path,
                caption=message
            )
            
            if success:
                logger.info(f"✅ Уведомление о готовности отчета отправлено пользователю {telegram_id}")
                
                # Если это бесплатный отчет, отправляем предложение премиум-отчета
                if not is_premium:
                    await self.send_premium_offer(telegram_id)
                
                return True

            # Фоллбэк: не удалось отправить файл — отправляем ссылку на скачивание
            logger.error(f"❌ Не удалось отправить файл пользователю {telegram_id}, отправляем ссылку")
            link_message = self._compose_link_message(is_premium, download_url)
            success = await self.send_message(telegram_id, link_message)
            
            # Если это бесплатный отчет, отправляем предложение премиум-отчета
            if success and not is_premium:
                await self.send_premium_offer(telegram_id)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления пользователю {telegram_id}: {e}")
            return False

    async def send_premium_offer(self, telegram_id: int) -> bool:
        """Отправить предложение премиум-отчета после бесплатного отчета"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, предложение премиум-отчета не отправлено")
            return False
            
        try:
            # Формируем сообщение с предложением
            message = f"""
🎁 <b>Ваша полная психологическая книга-расшифровка на 150 страниц, сейчас доступна по спеццене — всего 3.590 ₽ вместо 6.980 ₽.</b>

Успейте воспользоваться предложением прямо сейчас

PRIZMA – ваш личный тренер по развитию, доступный всегда, без ограничений по времени

Откройте глубокое понимание себя и план действий на годы вперёд

🔥 <b>Хотите получить по акции?</b>
            """.strip()
            
            # Путь к изображению премиум-отчета
            from pathlib import Path
            base_dir = Path(__file__).resolve().parent.parent
            image_path = base_dir / "image" / "example-premium.jpg"
            
            # Проверяем существование изображения
            if image_path.exists():
                logger.info(f"📸 Отправляем предложение с изображением: {image_path}")
                
                # Отправляем изображение с подписью и inline кнопкой (внутри Web App)
                keyboard = {
                    "inline_keyboard": [[
                        {
                            "text": "🔥 Хочу получить по акции!",
                            "web_app": {
                                "url": f"{self.webapp_url}/price-offer.html"
                            }
                        }
                    ]]
                }
                
                # Отправляем изображение с подписью и кнопкой
                success = await self.send_photo_with_keyboard(
                    chat_id=telegram_id,
                    photo_path=str(image_path),
                    caption=message,
                    keyboard=keyboard
                )
                
                if success:
                    logger.info(f"✅ Предложение премиум-отчета с изображением отправлено пользователю {telegram_id}")
                else:
                    logger.error(f"❌ Не удалось отправить предложение с изображением пользователю {telegram_id}")
                    
                return success
            else:
                logger.warning(f"⚠️ Изображение не найдено: {image_path}, отправляем текстовое предложение")
                
                # Фоллбэк: отправляем текстовое сообщение с кнопкой (внутри Web App)
                keyboard = {
                    "inline_keyboard": [[
                        {
                            "text": "🔥 Хочу получить по акции!",
                            "web_app": {
                                "url": f"{self.webapp_url}/price-offer.html"
                            }
                        }
                    ]]
                }
                
                success = await self.send_message_with_keyboard(telegram_id, message, keyboard)
                
                if success:
                    logger.info(f"✅ Предложение премиум-отчета (текст) отправлено пользователю {telegram_id}")
                else:
                    logger.error(f"❌ Не удалось отправить предложение премиум-отчета пользователю {telegram_id}")
                    
                return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке предложения премиум-отчета пользователю {telegram_id}: {e}")
            return False

    async def send_message_with_keyboard(self, chat_id: int, text: str, keyboard: dict, parse_mode: str = "HTML") -> bool:
        """Отправить текстовое сообщение с inline клавиатурой"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, сообщение с клавиатурой не отправлено")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "reply_markup": keyboard
                }
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info(f"✅ Сообщение с клавиатурой отправлено пользователю {chat_id}")
                            return True
                        else:
                            logger.error(f"❌ Ошибка отправки сообщения с клавиатурой: {result}")
                            return False
                    else:
                        logger.error(f"❌ HTTP ошибка при отправке сообщения с клавиатурой: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке сообщения с клавиатурой пользователю {chat_id}: {e}")
            return False

    async def send_photo_with_keyboard(self, chat_id: int, photo_path: str, caption: str = "", keyboard: dict = None, parse_mode: str = "HTML") -> bool:
        """Отправить изображение с inline клавиатурой"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, изображение с клавиатурой не отправлено")
            return False
            
        try:
            if not os.path.exists(photo_path):
                logger.error(f"❌ Файл изображения не найден: {photo_path}")
                return False
                
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendPhoto"
                
                with open(photo_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('chat_id', str(chat_id))
                    data.add_field('photo', file, filename=os.path.basename(photo_path))
                    if caption:
                        data.add_field('caption', caption)
                    if keyboard:
                        data.add_field('reply_markup', json.dumps(keyboard))
                    if parse_mode:
                        data.add_field('parse_mode', parse_mode)
                    
                    async with session.post(url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("ok"):
                                logger.info(f"✅ Изображение с клавиатурой отправлено пользователю {chat_id}: {os.path.basename(photo_path)}")
                                return True
                            else:
                                logger.error(f"❌ Ошибка отправки изображения с клавиатурой: {result}")
                                return False
                        else:
                            logger.error(f"❌ HTTP ошибка при отправке изображения с клавиатурой: {response.status}")
                            return False
                            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке изображения с клавиатурой пользователю {chat_id}: {e}")
            return False

    async def send_special_offer_6_hours_left(self, telegram_id: int) -> bool:
        """Отправить уведомление за 6 часов до конца акции"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, уведомление за 6 часов не отправлено")
            return False
            
        try:
            message = f"""
⏳ <b>До конца вашей скидки осталось всего 6 часов!</b>
Полный аудит вашей личности ещё доступен по акции 3.590 ₽ вместо 6.980 ₽

По цене одного сеанса у психолога вы получаете 150 страниц личностного аудита и персональные шаги для роста:

• 🧠 Глубокий психологический портрет с анализом Big Five и MBTI
• 🌀 Уникальные архетипы и когнитивный профиль, раскрывающие ваш внутренний потенциал
• 💡 Анализ эмоционального интеллекта и управления состояниями
• 🔮 Персональный прогноз развития и жизненных сценариев на 1–3 года
• 🌟 Выделение сильных сторон, талантов и ресурсных состояний для роста
• ⚖️ Индивидуальные стратегии компенсации зон роста и план действий
• 🤝 Практические рекомендации по взаимодействию с окружающими и развитию карьеры
• 🚀 Персональный мотивационный драйвер и эффективные техники принятия решений
• ❤️ Советы по улучшению отношений и управлению эмоциональными триггерами
• 📈 Индивидуальный план развития с упражнениями и ресурсами для устойчивых изменений
            """.strip()
            
            # Создаем inline кнопку для перехода к оплате (внутри Web App)
            keyboard = {
                "inline_keyboard": [[
                    {
                        "text": "🔥 Хочу получить начать трансформацию!",
                        "web_app": {
                            "url": f"{self.webapp_url}/price-offer.html"
                        }
                    }
                ]]
            }
            
            # Отправляем сообщение с кнопкой
            success = await self.send_message_with_keyboard(telegram_id, message, keyboard)
            
            if success:
                logger.info(f"✅ Уведомление за 6 часов до конца акции отправлено пользователю {telegram_id}")
            else:
                logger.error(f"❌ Не удалось отправить уведомление за 6 часов до конца акции пользователю {telegram_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления за 6 часов до конца акции пользователю {telegram_id}: {e}")
            return False

    async def send_special_offer_1_hour_left(self, telegram_id: int) -> bool:
        """Отправить уведомление за 1 час до конца акции"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, уведомление за 1 час не отправлено")
            return False
            
        try:
            message = f"""
⚡ <b>Последний шанс!</b>
У вас остался 1 час, чтобы получить свою полную расшифровку за 3.590 ₽
Дальше цена снова вырастет до 6.980 ₽

✨ Помните, это вложение в ваше понимание себя и ключ к вашему развитию.
🎯 Уже сотни людей сделали свой выбор — не упустите такую возможность!
🧭 Эта книга-анализ станет вашим личным путеводителем на пути к осознанной жизни, росту и процветанию
            """.strip()
            
            # Создаем inline кнопку для перехода к оплате (внутри Web App)
            keyboard = {
                "inline_keyboard": [[
                    {
                        "text": "🔥 Хочу изучить себя на 100%",
                        "web_app": {
                            "url": f"{self.webapp_url}/price-offer.html"
                        }
                    }
                ]]
            }
            
            # Отправляем сообщение с кнопкой
            success = await self.send_message_with_keyboard(telegram_id, message, keyboard)
            
            if success:
                logger.info(f"✅ Уведомление за 1 час до конца акции отправлено пользователю {telegram_id}")
            else:
                logger.error(f"❌ Не удалось отправить уведомление за 1 час до конца акции пользователю {telegram_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления за 1 час до конца акции пользователю {telegram_id}: {e}")
            return False

    async def send_special_offer_10_minutes_left(self, telegram_id: int) -> bool:
        """Отправить уведомление за 10 минут до конца акции"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, уведомление за 10 минут не отправлено")
            return False
            
        try:
            message = f"""
🚨 <b>Ваше спецпредложение закрывается!</b>
Вы больше не сможете получить полную расшифровку со скидкой –50% ☹️
            """.strip()
            
            # Создаем inline кнопку для перехода к оплате (внутри Web App)
            keyboard = {
                "inline_keyboard": [[
                    {
                        "text": "🔥 Успеть в последний вагон",
                        "web_app": {
                            "url": f"{self.webapp_url}/price-offer.html"
                        }
                    }
                ]]
            }
            
            # Отправляем сообщение с кнопкой
            success = await self.send_message_with_keyboard(telegram_id, message, keyboard)
            
            if success:
                logger.info(f"✅ Уведомление за 10 минут до конца акции отправлено пользователю {telegram_id}")
            else:
                logger.error(f"❌ Не удалось отправить уведомление за 10 минут до конца акции пользователю {telegram_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления за 10 минут до конца акции пользователю {telegram_id}: {e}")
            return False

    def _build_download_url(self, telegram_id: int, is_premium: bool) -> str:
        """Собрать абсолютный URL для скачивания отчета"""
        try:
            base = self.webapp_url or ""
            if not base:
                return ""
            path = f"/api/download/premium-report/{telegram_id}" if is_premium else f"/api/download/report/{telegram_id}"
            # download=1 принудит скачивание в Telegram Web App/браузере
            return f"{base}{path}?download=1"
        except Exception:
            return ""

    def _compose_link_message(self, is_premium: bool, url: str) -> str:
        """Сформировать текст сообщения со ссылкой на скачивание"""
        report_word = "Премиум-отчет" if is_premium else "Отчет"
        link_text = url or "в веб-приложении"
        return (
            f"🎉 <b>{report_word} готов!</b>\n\n"
            f"📥 <b>Скачать:</b> {link_text}\n\n"
            f"ℹ️ Если ссылка не открывается, скопируйте ее и откройте в браузере."
        )
    
    async def send_error_notification(self, telegram_id: int, error_message: str) -> bool:
        """Отправить уведомление об ошибке"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, уведомление об ошибке не отправлено")
            return False
            
        try:
            message = f"""
❌ <b>Произошла ошибка при генерации отчета</b>

🔧 Мы уже работаем над решением проблемы.

📝 Попробуйте снова через несколько минут или обратитесь в поддержку.

<i>Ошибка: {error_message}</i>
            """.strip()
            
            success = await self.send_message(telegram_id, message)
            
            if success:
                logger.info(f"✅ Уведомление об ошибке отправлено пользователю {telegram_id}")
            else:
                logger.error(f"❌ Не удалось отправить уведомление об ошибке пользователю {telegram_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления об ошибке пользователю {telegram_id}: {e}")
            return False

    async def set_webhook(self, webhook_url: str) -> bool:
        """Настроить webhook для получения обновлений от Telegram"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, webhook не настроен")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/setWebhook"
                data = {
                    "url": webhook_url
                }
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info(f"✅ Webhook успешно настроен: {webhook_url}")
                            return True
                        else:
                            logger.error(f"❌ Ошибка настройки webhook: {result}")
                            return False
                    else:
                        logger.error(f"❌ HTTP ошибка при настройке webhook: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке webhook: {e}")
            return False

    async def send_start_message(self, telegram_id: int) -> bool:
        """Отправить приветственное сообщение при команде /start (работает для всех пользователей)"""
        if not self.enabled:
            logger.warning("⚠️ Telegram отключен, приветственное сообщение не отправлено")
            return False
            
        try:
            message = f"""
👋 <b>Добро пожаловать в PRIZMA!</b>

Ваш личный ИИ психолог и наставник поможет вам:

🧠 Расшифровать вашу личность на 100%
📊 Получить глубокий психологический анализ
💡 Узнать свои сильные стороны и зоны роста
🚀 Получить персональный план развития

Начните свой путь к самопознанию прямо сейчас!
Откройте приложение для работы с ИИ психологом.
            """.strip()
            
            # Создаем inline кнопку для открытия Web App
            keyboard = {
                "inline_keyboard": [[
                    {
                        "text": "🚀 Начать тест",
                        "web_app": {
                            "url": f"{self.webapp_url}/index.html"
                        }
                    }
                ]]
            }
            
            success = await self.send_message_with_keyboard(telegram_id, message, keyboard)
            
            if success:
                logger.info(f"✅ Приветственное сообщение отправлено пользователю {telegram_id}")
            else:
                logger.error(f"❌ Не удалось отправить приветственное сообщение пользователю {telegram_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке приветственного сообщения пользователю {telegram_id}: {e}")
            return False

# Создаем глобальный экземпляр сервиса
telegram_service = TelegramService()
