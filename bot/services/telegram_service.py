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
                return await self.send_message(telegram_id, link_message)
            
            # Отправляем сообщение с файлом
            success = await self.send_document(
                chat_id=telegram_id,
                file_path=report_path,
                caption=message
            )
            
            if success:
                logger.info(f"✅ Уведомление о готовности отчета отправлено пользователю {telegram_id}")
                return True

            # Фоллбэк: не удалось отправить файл — отправляем ссылку на скачивание
            logger.error(f"❌ Не удалось отправить файл пользователю {telegram_id}, отправляем ссылку")
            link_message = self._compose_link_message(is_premium, download_url)
            return await self.send_message(telegram_id, link_message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления пользователю {telegram_id}: {e}")
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

# Создаем глобальный экземпляр сервиса
telegram_service = TelegramService()
