#!/usr/bin/env python3
"""
Скрипт для добавления колонки special_offer_started_at в таблицу users на сервере
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database.database import engine
from sqlalchemy import text

async def add_timer_column_server():
    """Добавление колонки таймера в таблицу users на сервере"""
    
    print("🔧 Добавление колонки special_offer_started_at в таблицу users на сервере")
    print("=" * 70)
    
    try:
        async with engine.begin() as conn:
            # Проверяем, существует ли колонка
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"📋 Существующие колонки: {column_names}")
            
            if 'special_offer_started_at' in column_names:
                print("✅ Колонка special_offer_started_at уже существует")
                return
            
            # Добавляем колонку
            print("➕ Добавление колонки special_offer_started_at...")
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN special_offer_started_at DATETIME
            """))
            
            print("✅ Колонка успешно добавлена")
            
            # Проверяем результат
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"📋 Обновленные колонки: {column_names}")
            
            # Проверяем, что колонка действительно добавлена
            if 'special_offer_started_at' in column_names:
                print("🎉 Колонка special_offer_started_at успешно добавлена в базу данных!")
            else:
                print("❌ Ошибка: колонка не была добавлена")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_timer_column_server())
