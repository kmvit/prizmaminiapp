from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()

class QuestionType(Enum):
    FREE = "free"
    PAID = "paid"

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReportGenerationStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    username = Column(String(100), nullable=True)
    language_code = Column(String(10), nullable=True)
    
    # Дополнительная информация профиля
    name = Column(String(100), nullable=True)  # Имя для опроса
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Статусы и настройки
    is_paid = Column(Boolean, default=False)
    is_premium_paid = Column(Boolean, default=False) # Добавляем новое поле для оплаты премиум отчета
    is_active = Column(Boolean, default=True)
    current_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    test_completed = Column(Boolean, default=False)
    
    # Статусы генерации отчетов
    free_report_status = Column(SQLEnum(ReportGenerationStatus), default=ReportGenerationStatus.PENDING)
    premium_report_status = Column(SQLEnum(ReportGenerationStatus), default=ReportGenerationStatus.PENDING)
    
    # Пути к готовым отчетам
    free_report_path = Column(String(500), nullable=True)
    premium_report_path = Column(String(500), nullable=True)
    
    # Ошибки генерации
    report_generation_error = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    test_started_at = Column(DateTime, nullable=True)
    test_completed_at = Column(DateTime, nullable=True)
    report_generation_started_at = Column(DateTime, nullable=True)
    report_generation_completed_at = Column(DateTime, nullable=True)
    
    # Таймер спецпредложения
    special_offer_started_at = Column(DateTime, nullable=True)
    
    # Связи
    answers = relationship("Answer", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    current_question = relationship("Question", foreign_keys=[current_question_id])

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    type = Column(SQLEnum(QuestionType), nullable=False, default=QuestionType.FREE)
    order_number = Column(Integer, nullable=False, unique=True)
    
    # Настройки вопроса
    is_active = Column(Boolean, default=True)
    allow_voice = Column(Boolean, default=True)
    max_length = Column(Integer, default=1000)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    
    # Содержимое ответа
    text_answer = Column(Text, nullable=True)
    voice_file_id = Column(String(200), nullable=True)  # Telegram file_id для голосового сообщения
    
    # ИИ анализ
    ai_analysis = Column(Text, nullable=True)
    analysis_status = Column(String(20), default="pending")  # pending, completed, failed
    
    # Метаданные
    answer_type = Column(String(20), default="text")  # text, voice
    processing_time = Column(Integer, nullable=True)  # время обработки в секундах
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Данные платежа
    amount = Column(Integer, nullable=False)  # сумма в копейках
    currency = Column(String(3), default="RUB")
    description = Column(String(255), nullable=True)
    
    # Robokassa данные
    invoice_id = Column(String(100), unique=True, nullable=False)
    robokassa_payment_id = Column(String(100), nullable=True)
    
    # Статус и результат
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="payments")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Содержимое отчета
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Файлы отчета
    pdf_file_path = Column(String(500), nullable=True)
    pdf_file_id = Column(String(200), nullable=True)  # Telegram file_id
    
    # Метаданные
    generation_status = Column(String(20), default="pending")  # pending, completed, failed
    version = Column(Integer, default=1)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User") 