#!/usr/bin/env python3
"""
Тест: генерация бесплатной психологической расшифровки (10 вопросов) и PDF-отчета
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime

from bot.database.models import User
from bot.services.perplexity import AIAnalysisService
from bot.services.pdf_service import ReportGenerator

# Моковые классы для теста (минимально необходимые)
class TestUser:
    def __init__(self, telegram_id=111111, first_name="Тест", last_name="Пользователь"):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = datetime.now()

class TestQuestion:
    def __init__(self, id, order_number, text, question_type="FREE"):
        self.id = id
        self.order_number = order_number
        self.text = text
        self.type = question_type

class TestAnswer:
    def __init__(self, question_id, text_answer):
        self.question_id = question_id
        self.text_answer = text_answer
        self.created_at = datetime.now()

def load_free_questions_and_answers():
    """Загружает первые 10 бесплатных вопросов и ответов из data/questions_with_answers.json"""
    path = Path("data/questions_with_answers.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = []
    answers = []
    for item in data["questions"]:
        if item["order_number"] > 10:
            break
        questions.append(TestQuestion(
            id=item["order_number"],
            order_number=item["order_number"],
            text=item["text"],
            question_type=item["type"]
        ))
        answers.append(TestAnswer(
            question_id=item["order_number"],
            text_answer=item["answer"]
        ))
    return questions, answers

async def test_free_psychology_pdf():
    print("=== ТЕСТ: Бесплатная расшифровка + PDF ===")
    user = TestUser()
    questions, answers = load_free_questions_and_answers()
    print(f"Вопросов: {len(questions)}, ответов: {len(answers)}")
    ai_service = AIAnalysisService()
    report_generator = ReportGenerator()
    # Генерируем анализ
    analysis_result = await ai_service.generate_psychological_report(user, questions, answers)
    assert analysis_result["success"], f"Ошибка анализа: {analysis_result.get('error')}"
    print("AI-анализ успешно сгенерирован!")
    # Генерируем PDF
    pdf_path = report_generator.create_pdf_report(user, analysis_result)
    assert pdf_path and Path(pdf_path).exists(), "PDF не создан!"
    print(f"PDF успешно создан: {pdf_path}")
    size_kb = Path(pdf_path).stat().st_size / 1024
    print(f"Размер PDF: {size_kb:.1f} KB")

if __name__ == "__main__":
    asyncio.run(test_free_psychology_pdf()) 