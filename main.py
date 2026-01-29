#!/usr/bin/env python3
"""
Основной файл запуска PRIZMA - веб-приложение для психологического тестирования с ИИ-анализом
"""

import asyncio
import sys
import logging
from pathlib import Path

import uvicorn
from bot.database.database import init_db
from loguru import logger

# Настройка логирования для подавления предупреждений о некорректных HTTP запросах
# Применяем фильтр после импорта uvicorn, но до запуска сервера
def setup_uvicorn_logging():
    """Настройка логирования uvicorn для подавления некорректных HTTP запросов"""
    class InvalidRequestFilter(logging.Filter):
        """Фильтр для подавления только предупреждений о некорректных HTTP запросах"""
        def filter(self, record):
            message = str(record.getMessage())
            # Подавляем только конкретные предупреждения о некорректных HTTP запросах
            if "Invalid HTTP request received" in message:
                return False
            # Все остальные сообщения пропускаем
            return True
    
    # Применяем фильтр ко всем логгерам uvicorn
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.addFilter(InvalidRequestFilter())

async def initialize_database():
    """Инициализация базы данных"""
    try:
        logger.info("📊 Инициализация базы данных...")
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
        raise

def start_server():
    """Запуск сервера"""
    try:
        # Инициализируем базу данных
        asyncio.run(initialize_database())
        
        logger.info("🚀 Запуск FastAPI сервера PRIZMA...")
        logger.info("📱 API документация: http://0.0.0.0:8080/docs")
        logger.info("📖 ReDoc документация: http://0.0.0.0:8080/redoc")
        logger.info("🌐 Фронтенд: http://0.0.0.0:8080/")
        logger.info("❓ Проверка работы: http://0.0.0.0:8080/api/health")
        logger.info("ℹ️  Сервер доступен локально: http://localhost:8080/")
        logger.info("⏹️  Для остановки нажмите Ctrl+C")
        
        # Настраиваем логирование uvicorn перед запуском
        setup_uvicorn_logging()
        
        # Запускаем uvicorn
        # Предупреждения "Invalid HTTP request received" будут скрыты благодаря настройке logging выше
        uvicorn.run(
            "bot.web_app:app",
            host="0.0.0.0",
            port=8080,
            reload=True,  # Автоперезагрузка при изменении кода
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()