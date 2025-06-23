from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class QuestionType(Enum):
    FREE = "free"
    PAID = "paid"

@dataclass
class Question:
    id: int
    text: str
    type: QuestionType

class QuestionService:
    def __init__(self):
        self.questions: Dict[int, Question] = {}
        self._initialize_questions()

    def _initialize_questions(self):
        # TODO: В будущем можно загружать из базы данных или конфига
        questions = [
            Question(1, "Как вы обычно реагируете на стрессовые ситуации?", QuestionType.FREE),
            Question(2, "Опишите ваш идеальный день.", QuestionType.FREE),
            # ... добавить остальные вопросы
        ]
        for question in questions:
            self.questions[question.id] = question

    def get_question(self, question_id: int) -> Question:
        return self.questions.get(question_id)

    def get_next_question(self, current_id: int, is_paid: bool) -> Question:
        """Получить следующий вопрос на основе текущего ID и типа подписки"""
        for q_id in range(current_id + 1, len(self.questions) + 1):
            question = self.questions[q_id]
            if is_paid or question.type == QuestionType.FREE:
                return question
        return None

    def get_total_questions(self, is_paid: bool) -> int:
        """Получить общее количество вопросов для типа подписки"""
        if is_paid:
            return len(self.questions)
        return len([q for q in self.questions.values() if q.type == QuestionType.FREE])

# Создаем экземпляр сервиса
question_service = QuestionService() 