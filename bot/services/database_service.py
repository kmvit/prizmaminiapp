from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from bot.database.models import User, Question, Answer, Payment, Report, QuestionType, PaymentStatus
from bot.database.database import async_session
from bot.config import FREE_QUESTIONS_LIMIT

class DatabaseService:
    
    async def get_session(self) -> AsyncSession:
        """Получить сессию базы данных"""
        async with async_session() as session:
            return session
    
    # --- Работа с пользователями ---
    
    async def get_or_create_user(self, telegram_id: int, **user_data) -> User:
        """Получить пользователя или создать нового"""
        async with async_session() as session:
            # Ищем существующего пользователя
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # Создаем нового пользователя
                user = User(
                    telegram_id=telegram_id,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name'),
                    username=user_data.get('username'),
                    language_code=user_data.get('language_code')
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            return user
    
    async def update_user_profile(self, telegram_id: int, name: str = None, age: int = None, gender: str = None) -> User:
        """Обновить профиль пользователя"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            if name:
                user.name = name
            if age:
                user.age = age
            if gender:
                user.gender = gender
            
            user.updated_at = datetime.utcnow()
            await session.commit()
            return user
    
    async def start_test(self, telegram_id: int) -> User:
        """Начать тест для пользователя"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            # Если пользователь уже проходил тест - удаляем старые ответы
            if user.test_completed or user.current_question_id:
                deleted_count = await self.clear_user_answers(telegram_id)
                from loguru import logger
                logger.info(f"🗑️ Удалено {deleted_count} старых ответов для пользователя {telegram_id}")
            
            # Получаем первый вопрос
            first_question = await self.get_first_question()
            
            user.current_question_id = first_question.id
            user.test_started_at = datetime.utcnow()
            user.test_completed = False
            user.test_completed_at = None  # Сбрасываем время завершения
            
            await session.commit()
            return user
    
    async def complete_test(self, telegram_id: int) -> User:
        """Завершить тест для пользователя"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            user.test_completed = True
            user.test_completed_at = datetime.utcnow()
            user.current_question_id = None
            
            await session.commit()
            return user
    
    async def upgrade_to_paid(self, telegram_id: int) -> User:
        """Обновить пользователя до платной версии"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            user.is_paid = True
            user.updated_at = datetime.utcnow()
            
            await session.commit()
            return user
    
    # --- Работа с вопросами ---
    
    async def get_first_question(self) -> Question:
        """Получить первый вопрос"""
        async with async_session() as session:
            stmt = select(Question).where(Question.is_active == True).order_by(Question.order_number).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one()
    
    async def get_question(self, question_id: int) -> Optional[Question]:
        """Получить вопрос по ID"""
        async with async_session() as session:
            stmt = select(Question).where(Question.id == question_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_next_question(self, current_question_id: int, is_paid: bool) -> Optional[Question]:
        """Получить следующий вопрос"""
        async with async_session() as session:
            # Получаем текущий вопрос для определения order_number
            current_stmt = select(Question).where(Question.id == current_question_id)
            current_result = await session.execute(current_stmt)
            current_question = current_result.scalar_one_or_none()
            
            if not current_question:
                return None
            
            # Формируем условия для поиска следующего вопроса
            conditions = [
                Question.order_number > current_question.order_number,
                Question.is_active == True
            ]
            
            # Если пользователь не платный, ограничиваем первыми N вопросами
            if not is_paid:
                conditions.append(Question.order_number <= FREE_QUESTIONS_LIMIT)
            
            stmt = select(Question).where(and_(*conditions)).order_by(Question.order_number).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_total_questions(self, is_paid: bool) -> int:
        """Получить общее количество вопросов"""
        if not is_paid:
            return FREE_QUESTIONS_LIMIT
            
        async with async_session() as session:
            conditions = [Question.is_active == True]
            
            stmt = select(Question).where(and_(*conditions))
            result = await session.execute(stmt)
            questions = result.scalars().all()
            return len(questions)
    
    async def get_questions(self) -> List[Question]:
        """Получить все активные вопросы"""
        async with async_session() as session:
            stmt = select(Question).where(Question.is_active == True).order_by(Question.order_number)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def create_question(self, text: str, question_type: QuestionType, order_number: int) -> Question:
        """Создать новый вопрос"""
        async with async_session() as session:
            question = Question(
                text=text,
                type=question_type,
                order_number=order_number
            )
            session.add(question)
            await session.commit()
            await session.refresh(question)
            return question
    
    # --- Работа с ответами ---
    
    async def save_answer(self, telegram_id: int, question_id: int, text_answer: str = None, 
                         voice_file_id: str = None, answer_type: str = "text") -> Answer:
        """Сохранить ответ пользователя"""
        async with async_session() as session:
            # Получаем пользователя
            user_stmt = select(User).where(User.telegram_id == telegram_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one()
            
            answer = Answer(
                user_id=user.id,
                question_id=question_id,
                text_answer=text_answer,
                voice_file_id=voice_file_id,
                answer_type=answer_type
            )
            
            session.add(answer)
            await session.commit()
            await session.refresh(answer)
            return answer
    
    async def update_answer_analysis(self, answer_id: int, ai_analysis: str) -> Answer:
        """Обновить анализ ответа"""
        async with async_session() as session:
            stmt = select(Answer).where(Answer.id == answer_id)
            result = await session.execute(stmt)
            answer = result.scalar_one()
            
            answer.ai_analysis = ai_analysis
            answer.analysis_status = "completed"
            answer.analyzed_at = datetime.utcnow()
            
            await session.commit()
            return answer
    
    async def clear_user_answers(self, telegram_id: int) -> int:
        """Удалить все ответы пользователя"""
        async with async_session() as session:
            # Получаем пользователя
            user_stmt = select(User).where(User.telegram_id == telegram_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one()
            
            # Удаляем все ответы пользователя
            from sqlalchemy import delete
            stmt = delete(Answer).where(Answer.user_id == user.id)
            result = await session.execute(stmt)
            deleted_count = result.rowcount
            
            await session.commit()
            return deleted_count

    async def get_user_answers(self, telegram_id: int) -> List[Answer]:
        """Получить все ответы пользователя"""
        async with async_session() as session:
            user_stmt = select(User).where(User.telegram_id == telegram_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one()
            
            stmt = select(Answer).options(
                selectinload(Answer.question)
            ).where(Answer.user_id == user.id).order_by(Answer.created_at)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    # --- Работа с платежами ---
    
    async def create_payment(self, telegram_id: int, amount: int, invoice_id: str, description: str = None) -> Payment:
        """Создать платеж"""
        async with async_session() as session:
            user_stmt = select(User).where(User.telegram_id == telegram_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one()
            
            payment = Payment(
                user_id=user.id,
                amount=amount,
                invoice_id=invoice_id,
                description=description
            )
            
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            return payment
    
    async def update_payment_status(self, invoice_id: str, status: PaymentStatus, 
                                  robokassa_payment_id: str = None) -> Payment:
        """Обновить статус платежа"""
        async with async_session() as session:
            stmt = select(Payment).where(Payment.invoice_id == invoice_id)
            result = await session.execute(stmt)
            payment = result.scalar_one()
            
            payment.status = status
            if robokassa_payment_id:
                payment.robokassa_payment_id = robokassa_payment_id
            if status == PaymentStatus.COMPLETED:
                payment.paid_at = datetime.utcnow()
            
            await session.commit()
            return payment
    
    # --- Работа с отчетами ---
    
    async def create_report(self, telegram_id: int, content: str, summary: str = None) -> Report:
        """Создать отчет"""
        async with async_session() as session:
            user_stmt = select(User).where(User.telegram_id == telegram_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one()
            
            report = Report(
                user_id=user.id,
                content=content,
                summary=summary
            )
            
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return report
    
    async def update_report_files(self, report_id: int, pdf_file_path: str = None, 
                                pdf_file_id: str = None) -> Report:
        """Обновить файлы отчета"""
        async with async_session() as session:
            stmt = select(Report).where(Report.id == report_id)
            result = await session.execute(stmt)
            report = result.scalar_one()
            
            if pdf_file_path:
                report.pdf_file_path = pdf_file_path
            if pdf_file_id:
                report.pdf_file_id = pdf_file_id
            
            report.generation_status = "completed"
            report.generated_at = datetime.utcnow()
            
            await session.commit()
            return report

# Создаем экземпляр сервиса
db_service = DatabaseService() 