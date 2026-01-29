#!/usr/bin/env python3
"""
Простой скрипт для загрузки вопросов в базу данных PRIZMA
Запуск: python bot/database/seed_data.py
"""

import asyncio
import json
import sys
from pathlib import Path
from sqlalchemy import delete

# Добавляем корневую директорию проекта в Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from bot.database.database import init_db, async_session
from bot.database.models import Question, QuestionType

async def load_questions():
    """Загрузить вопросы из двух JSON файлов (бесплатные и платные) в базу данных"""
    
    # Пути к JSON файлам
    data_dir = Path(__file__).parent.parent.parent / "data"
    free_json_path = data_dir / "questions_free.json"
    premium_json_path = data_dir / "questions_premium.json"
    
    print("🔬 PRIZMA - Загрузка вопросов в базу данных")
    print("=" * 50)
    
    # Читаем оба JSON файла
    all_questions = []
    
    try:
        # Загружаем бесплатные вопросы
        with open(free_json_path, 'r', encoding='utf-8') as f:
            free_data = json.load(f)
        free_questions = free_data["questions"]
        print(f"📋 Найдено {len(free_questions)} бесплатных вопросов")
        all_questions.extend(free_questions)
        
        # Загружаем платные вопросы
        with open(premium_json_path, 'r', encoding='utf-8') as f:
            premium_data = json.load(f)
        premium_questions = premium_data["questions"]
        print(f"📋 Найдено {len(premium_questions)} платных вопросов")
        all_questions.extend(premium_questions)
        
    except Exception as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return
    
    async with async_session() as session:
        try:
            # Очищаем старые вопросы
            await session.execute(delete(Question))
            print("🗑️ Очищены старые вопросы")
            
            # Добавляем новые вопросы
            free_count = 0
            premium_count = 0
            current_order = 1  # Глобальный порядковый номер
            
            # Сначала добавляем бесплатные вопросы (1-8)
            for q_data in free_questions:
                question_type = QuestionType.FREE
                
                question = Question(
                    text=q_data["text"],
                    type=question_type,
                    test_version="free",
                    order_number=current_order,
                    allow_voice=q_data.get("allow_voice", True),
                    max_length=q_data.get("max_length", 1000)
                )
                session.add(question)
                free_count += 1
                current_order += 1
            
            # Затем добавляем платные вопросы (9-46)
            for q_data in premium_questions:
                question_type = QuestionType.PAID
                
                question = Question(
                    text=q_data["text"],
                    type=question_type,
                    test_version="premium",
                    order_number=current_order,
                    allow_voice=q_data.get("allow_voice", True),
                    max_length=q_data.get("max_length", 1000)
                )
                session.add(question)
                premium_count += 1
                current_order += 1
            
            await session.commit()
            
            print("✅ Вопросы успешно загружены!")
            print(f"🆓 Бесплатных (free): {free_count}")
            print(f"💎 Платных (premium): {premium_count}")
            print(f"📝 Всего: {len(all_questions)}")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            await session.rollback()

async def main():
    """Инициализация БД и загрузка данных"""
    print("🚀 Инициализация базы данных...")
    await init_db()
    print("📊 Таблицы созданы")
    
    await load_questions()
    print("🎉 Готово! Можно запускать приложение")

if __name__ == "__main__":
    asyncio.run(main()) 