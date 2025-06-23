from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserAnswer:
    question_id: int
    answer: str
    analysis: str
    timestamp: datetime

class UserStateService:
    def __init__(self):
        self.user_states: Dict[int, Dict] = {}  # user_id -> state
        self.user_answers: Dict[int, List[UserAnswer]] = {}  # user_id -> answers

    def initialize_user(self, user_id: int, is_paid: bool = False):
        """Инициализировать состояние пользователя"""
        self.user_states[user_id] = {
            "current_question_id": 1,
            "is_paid": is_paid,
            "started_at": datetime.now(),
            "completed": False
        }
        self.user_answers[user_id] = []

    def get_user_state(self, user_id: int) -> Dict:
        """Получить состояние пользователя"""
        return self.user_states.get(user_id)

    def save_answer(self, user_id: int, question_id: int, answer: str, analysis: str):
        """Сохранить ответ пользователя и его анализ"""
        if user_id not in self.user_answers:
            self.user_answers[user_id] = []
        
        self.user_answers[user_id].append(
            UserAnswer(
                question_id=question_id,
                answer=answer,
                analysis=analysis,
                timestamp=datetime.now()
            )
        )

    def get_user_answers(self, user_id: int) -> List[UserAnswer]:
        """Получить все ответы пользователя"""
        return self.user_answers.get(user_id, [])

    def update_question_id(self, user_id: int, question_id: int):
        """Обновить текущий ID вопроса"""
        if user_id in self.user_states:
            self.user_states[user_id]["current_question_id"] = question_id

    def mark_completed(self, user_id: int):
        """Отметить тест как завершенный"""
        if user_id in self.user_states:
            self.user_states[user_id]["completed"] = True

# Создаем экземпляр сервиса
user_state_service = UserStateService() 