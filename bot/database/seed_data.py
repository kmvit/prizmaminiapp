#!/usr/bin/env python3
"""
Простой скрипт для загрузки вопросов в базу данных PRIZMA
Запуск: python -m bot.database.seed_data
"""

import asyncio
import json
from pathlib import Path
from sqlalchemy import delete
from bot.database.database import init_db, async_session
from bot.database.models import Question, QuestionType

async def load_questions():
    """Загрузить все вопросы из JSON в базу данных"""
    
    # Путь к JSON файлу
    json_path = Path(__file__).parent.parent.parent / "data" / "questions.json"
    
    print("🔬 PRIZMA - Загрузка вопросов в базу данных")
    print("=" * 50)
    
    # Читаем JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        questions_data = data["questions"]
        print(f"📋 Найдено {len(questions_data)} вопросов в JSON файле")
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
            paid_count = 0
            
            for q_data in questions_data:
                question_type = QuestionType.FREE if q_data["type"] == "FREE" else QuestionType.PAID
                
                question = Question(
                    text=q_data["text"],
                    type=question_type,
                    order_number=q_data["order_number"],
                    allow_voice=q_data.get("allow_voice", True),
                    max_length=q_data.get("max_length", 1000)
                )
                session.add(question)
                
                if question_type == QuestionType.FREE:
                    free_count += 1
                else:
                    paid_count += 1
            
            await session.commit()
            
            print("✅ Вопросы успешно загружены!")
            print(f"🆓 Бесплатных: {free_count}")
            print(f"💎 Платных: {paid_count}")
            print(f"📝 Всего: {len(questions_data)}")
            
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