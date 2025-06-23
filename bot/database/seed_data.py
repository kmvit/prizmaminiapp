import asyncio
from bot.database.database import init_db
from bot.database.models import Question, QuestionType
from bot.services.database_service import db_service

async def seed_questions():
    """Заполнить базу данных начальными вопросами"""
    
    questions_data = [
        # Бесплатные вопросы
        {
            "text": "Расскажите о себе. Как бы вы описали свою личность?",
            "type": QuestionType.FREE,
            "order_number": 1
        },
        {
            "text": "Как вы обычно реагируете на стрессовые ситуации? Приведите пример.",
            "type": QuestionType.FREE,
            "order_number": 2
        },
        {
            "text": "Опишите ваш идеальный день от утра до вечера.",
            "type": QuestionType.FREE,
            "order_number": 3
        },
        {
            "text": "Что вас больше всего мотивирует в жизни? Какие цели вы ставите перед собой?",
            "type": QuestionType.FREE,
            "order_number": 4
        },
        {
            "text": "Как вы принимаете важные решения? Полагаетесь на логику или интуицию?",
            "type": QuestionType.FREE,
            "order_number": 5
        },
        
        # Платные вопросы (более глубокие)
        {
            "text": "Расскажите о самом сложном периоде в вашей жизни. Как вы его преодолели?",
            "type": QuestionType.PAID,
            "order_number": 6
        },
        {
            "text": "Что вас больше всего пугает в отношениях с людьми? Как это влияет на вашу жизнь?",
            "type": QuestionType.PAID,
            "order_number": 7
        },
        {
            "text": "Опишите ваши детские воспоминания. Какие события сформировали вас как личность?",
            "type": QuestionType.PAID,
            "order_number": 8
        },
        {
            "text": "Как вы справляетесь с критикой? Расскажите о случае, когда критика сильно на вас повлияла.",
            "type": QuestionType.PAID,
            "order_number": 9
        },
        {
            "text": "Что вы чувствуете, когда остаетесь наедине с собой? О чем думаете в моменты одиночества?",
            "type": QuestionType.PAID,
            "order_number": 10
        },
        {
            "text": "Опишите ваши самые глубокие страхи и как они влияют на ваши жизненные выборы.",
            "type": QuestionType.PAID,
            "order_number": 11
        },
        {
            "text": "Как вы определяете успех? Что для вас значит быть счастливым?",
            "type": QuestionType.PAID,
            "order_number": 12
        },
        {
            "text": "Расскажите о ваших отношениях с родителями. Как это повлияло на ваш характер?",
            "type": QuestionType.PAID,
            "order_number": 13
        },
        {
            "text": "Что вы больше всего цените в других людях? А что вас раздражает?",
            "type": QuestionType.PAID,
            "order_number": 14
        },
        {
            "text": "Как вы видите себя через 10 лет? Какой человек, каких достижений, какой образ жизни?",
            "type": QuestionType.PAID,
            "order_number": 15
        }
    ]
    
    print("🌱 Начинаю заполнение базы данных вопросами...")
    
    for question_data in questions_data:
        try:
            await db_service.create_question(
                text=question_data["text"],
                question_type=question_data["type"],
                order_number=question_data["order_number"]
            )
            print(f"✅ Добавлен вопрос {question_data['order_number']}: {question_data['text'][:50]}...")
        except Exception as e:
            print(f"❌ Ошибка при добавлении вопроса {question_data['order_number']}: {e}")
    
    print("🎉 Заполнение базы данных завершено!")

async def main():
    """Инициализация базы данных и заполнение начальными данными"""
    print("🚀 Инициализация базы данных...")
    
    # Создаем таблицы
    await init_db()
    print("📝 Таблицы созданы")
    
    # Заполняем начальными данными
    await seed_questions()

if __name__ == "__main__":
    asyncio.run(main()) 