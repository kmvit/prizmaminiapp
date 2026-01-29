from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Модели запросов
class AnswerRequest(BaseModel):
    text_answer: str = Field(..., min_length=350, max_length=5000, description="Текст ответа пользователя")
    answer_type: str = Field(default="text", description="Тип ответа: text или voice")

class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="Имя пользователя")
    age: Optional[int] = Field(None, ge=1, le=120, description="Возраст пользователя")
    gender: Optional[str] = Field(None, max_length=20, description="Пол пользователя")

# Модели ответов
class QuestionResponse(BaseModel):
    id: int
    text: str
    order_number: int
    type: str
    allow_voice: bool
    max_length: int

class ProgressResponse(BaseModel):
    current: int
    total: int
    answered: int

class UserStatusResponse(BaseModel):
    is_paid: bool
    test_completed: bool

class CurrentQuestionResponse(BaseModel):
    question: QuestionResponse
    progress: ProgressResponse
    user: UserStatusResponse

class NextQuestionResponse(BaseModel):
    status: str = Field(..., description="next_question или test_completed")
    next_question: Optional[QuestionResponse] = None
    progress: Optional[ProgressResponse] = None
    message: Optional[str] = None

class UserProgressResponse(BaseModel):
    user: dict
    progress: dict
    answers: list

class UserProfileResponse(BaseModel):
    status: str
    user: dict
    payment_status: Optional[str] = Field(None, description="Статус оплаты: completed, pending, или None")

# Модели ошибок
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None 