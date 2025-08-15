from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
import decimal

from bot.database.models import User, Question, Answer, Payment, Report, QuestionType, PaymentStatus, ReportGenerationStatus
from bot.database.database import async_session
from bot.config import FREE_QUESTIONS_LIMIT
from bot.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseService:
    
    async def get_session(self) -> AsyncSession:
        """Получить сессию базы данных"""
        async with async_session() as session:
            return session
    
    # --- Работа с пользователями ---
    
    async def get_or_create_user(self, telegram_id: int, **user_data) -> User:
        """Получить пользователя или создать нового"""
        async with async_session() as session:
            try:
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
                else:
                    # Если пользователь найден, просто возвращаем его без коммита
                    await session.refresh(user)
                
                return user
            except Exception as e:
                await session.rollback()
                raise e
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def delete_user(self, telegram_id: int) -> bool:
        """Удалить пользователя и все связанные данные"""
        async with async_session() as session:
            try:
                # Находим пользователя
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    return False
                
                # Удаляем все связанные данные
                from bot.database.models import Answer, Payment, Report
                
                # Удаляем ответы
                await session.execute(Answer.__table__.delete().where(Answer.user_id == user.id))
                
                # Удаляем платежи
                await session.execute(Payment.__table__.delete().where(Payment.user_id == user.id))
                
                # Удаляем отчеты
                await session.execute(Report.__table__.delete().where(Report.user_id == user.id))
                
                # Удаляем пользователя
                await session.delete(user)
                await session.commit()
                
                return True
            except Exception as e:
                await session.rollback()
                raise e
    
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
            
            # НЕ удаляем старые ответы здесь - они нужны для генерации отчета
            # Ответы будут удалены только после успешной генерации отчета
            
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
    
    async def update_user_premium_status(self, telegram_id: int, is_premium_paid: bool) -> User:
        """Обновить статус is_premium_paid пользователя"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            user.is_premium_paid = is_premium_paid
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
    
    async def clear_user_data_after_report_generation(self, telegram_id: int) -> int:
        """Очистить данные пользователя после успешной генерации отчета"""
        async with async_session() as session:
            # Получаем пользователя
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            # Очищаем ответы только для бесплатных пользователей
            if not user.is_paid:
                deleted_count = await self.clear_user_answers(telegram_id)
                from loguru import logger
                logger.info(f"🗑️ Удалено {deleted_count} ответов после генерации отчета для пользователя {telegram_id}")
                return deleted_count
            else:
                # Для платных пользователей не удаляем ответы
                from loguru import logger
                logger.info(f"💎 Для платного пользователя {telegram_id} ответы не удаляются")
                return 0

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
    
    async def create_payment(self, user_id: int, amount: decimal.Decimal, currency: str, description: str, invoice_id: str, status: PaymentStatus) -> Payment:
        """Создать платеж"""
        async with async_session() as session:
            payment = Payment(
                user_id=user_id,
                amount=amount,
                currency=currency,
                description=description,
                invoice_id=invoice_id,
                status=status
            )
            
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            return payment
    
    async def get_payment_by_invoice_id(self, invoice_id: str) -> Optional[Payment]:
        """Получить платеж по invoice_id"""
        async with async_session() as session:
            stmt = select(Payment).where(Payment.invoice_id == invoice_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_payment_status(self, payment_id: int, status: PaymentStatus, 
                                  robokassa_payment_id: str = None) -> Payment:
        """Обновить статус платежа"""
        async with async_session() as session:
            stmt = select(Payment).where(Payment.id == payment_id)
            result = await session.execute(stmt)
            payment = result.scalar_one()
            
            payment.status = status
            if robokassa_payment_id:
                payment.robokassa_payment_id = robokassa_payment_id
            if status == PaymentStatus.COMPLETED:
                payment.paid_at = datetime.utcnow()
            
            await session.commit()
            return payment
    
    async def update_payment_invoice_id(self, payment_id: int, invoice_id: str):
        from bot.database.database import async_session
        from bot.database.models import Payment
        from sqlalchemy import update as sql_update

        async with async_session() as session:
            stmt = sql_update(Payment).where(Payment.id == payment_id).values(invoice_id=invoice_id)
            await session.execute(stmt)
            await session.commit()
    
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
            
            await session.commit()
            return report
    
    # --- Методы для работы со статусом генерации отчетов ---
    
    async def update_report_generation_status(self, telegram_id: int, report_type: str, 
                                            status: ReportGenerationStatus, 
                                            report_path: str = None, 
                                            error: str = None) -> User:
        """Обновить статус генерации отчета"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            
            logger.info(f"🔄 Обновление статуса отчета для пользователя {telegram_id}, тип: {report_type}, новый статус: {status.value}")
            
            if report_type == "free":
                user.free_report_status = status
                if report_path:
                    user.free_report_path = report_path
            elif report_type == "premium":
                user.premium_report_status = status
                if report_path:
                    user.premium_report_path = report_path
            
            if error:
                user.report_generation_error = error
            
            # Обновляем временные метки
            if status == ReportGenerationStatus.PROCESSING:
                user.report_generation_started_at = datetime.utcnow()
            elif status in [ReportGenerationStatus.COMPLETED, ReportGenerationStatus.FAILED]:
                user.report_generation_completed_at = datetime.utcnow()
            
            user.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"✅ Статус отчета обновлен для пользователя {telegram_id}, тип: {report_type}, статус: {status.value}")
            return user
    
    async def get_report_generation_status(self, telegram_id: int, report_type: str) -> dict:
        """Получить статус генерации отчета"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"⚠️ Пользователь {telegram_id} не найден при получении статуса отчета")
                return {"status": "user_not_found"}
            
            if report_type == "free":
                status_info = {
                    "status": user.free_report_status.value,
                    "report_path": user.free_report_path,
                    "error": user.report_generation_error,
                    "started_at": user.report_generation_started_at,
                    "completed_at": user.report_generation_completed_at
                }
                logger.info(f"📊 Статус бесплатного отчета для пользователя {telegram_id}: {status_info}")
                return status_info
            elif report_type == "premium":
                status_info = {
                    "status": user.premium_report_status.value,
                    "report_path": user.premium_report_path,
                    "error": user.report_generation_error,
                    "started_at": user.report_generation_started_at,
                    "completed_at": user.report_generation_completed_at
                }
                logger.info(f"📊 Статус премиум отчета для пользователя {telegram_id}: {status_info}")
                return status_info
            
            logger.warning(f"⚠️ Неизвестный тип отчета: {report_type} для пользователя {telegram_id}")
            return {"status": "invalid_report_type"}
    
    async def is_report_generating(self, telegram_id: int, report_type: str) -> bool:
        """Проверить, генерируется ли отчет"""
        status_info = await self.get_report_generation_status(telegram_id, report_type)
        is_generating = status_info.get("status") == ReportGenerationStatus.PROCESSING.value
        logger.info(f"🔍 Проверка генерации отчета для пользователя {telegram_id}, тип: {report_type}, статус: {status_info.get('status')}, генерируется: {is_generating}")
        return is_generating
    
    async def reset_user_after_premium_report(self, telegram_id: int) -> bool:
        """Сбросить состояние пользователя после отправки премиум-отчета в бот.
        - Сбросить ответы
        - Сбросить статусы отчетов
        - Перевести пользователя в бесплатный статус (is_paid = False)
        - Сбросить состояние теста
        История платежей при этом НЕ меняется.
        """
        async with async_session() as session:
            try:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"⚠️ Пользователь {telegram_id} не найден при сбросе состояния")
                    return False
                
                # 1) Удаляем ответы пользователя
                from sqlalchemy import delete
                await session.execute(delete(Answer).where(Answer.user_id == user.id))
                
                # 2) Сбрасываем статусы отчетов
                from bot.database.models import ReportGenerationStatus as RGS
                user.free_report_status = RGS.PENDING
                user.premium_report_status = RGS.PENDING
                user.free_report_path = None
                user.premium_report_path = None
                user.report_generation_error = None
                user.report_generation_started_at = None
                user.report_generation_completed_at = None
                
                # 3) Переводим пользователя в бесплатный статус
                user.is_paid = False
                if hasattr(user, "is_premium_paid"):
                    user.is_premium_paid = False
                
                # 4) Сбрасываем состояние теста
                user.test_completed = False
                user.test_started_at = None
                user.test_completed_at = None
                user.current_question_id = None
                
                user.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"✅ Состояние пользователя {telegram_id} успешно сброшено после отправки премиум-отчета")
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Ошибка при сбросе состояния пользователя {telegram_id}: {e}")
                raise e
    
    async def clear_report_statuses(self, telegram_id: int) -> bool:
        """Очистить статусы отчетов пользователя"""
        async with async_session() as session:
            try:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    return False
                
                # Сбрасываем статусы отчетов
                from bot.database.models import ReportGenerationStatus
                
                user.free_report_status = ReportGenerationStatus.PENDING
                user.free_report_path = None
                user.report_generation_error = None
                
                user.premium_report_status = ReportGenerationStatus.PENDING
                user.premium_report_path = None
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise e
    
    async def reset_stuck_reports(self, telegram_id: int) -> bool:
        """Сбросить зависшие отчеты (которые в статусе PROCESSING слишком долго)"""
        async with async_session() as session:
            try:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"⚠️ Пользователь {telegram_id} не найден при сбросе зависших отчетов")
                    return False
                
                from bot.database.models import ReportGenerationStatus
                from datetime import datetime, timedelta
                
                logger.info(f"🔍 Проверка зависших отчетов для пользователя {telegram_id}")
                logger.info(f"📊 Статус бесплатного отчета: {user.free_report_status}")
                logger.info(f"📊 Статус премиум отчета: {user.premium_report_status}")
                logger.info(f"⏰ Время начала генерации: {user.report_generation_started_at}")
                
                # Проверяем, не завис ли отчет в статусе PROCESSING
                if user.report_generation_started_at:
                    # Если отчет генерируется больше 30 минут, считаем его зависшим
                    time_diff = datetime.utcnow() - user.report_generation_started_at
                    logger.info(f"⏱️ Время с начала генерации: {time_diff}")
                    
                    if time_diff > timedelta(minutes=30):
                        logger.warning(f"⚠️ Сбрасываем зависший отчет для пользователя {telegram_id} (время генерации: {time_diff})")
                        
                        if user.free_report_status == ReportGenerationStatus.PROCESSING:
                            user.free_report_status = ReportGenerationStatus.PENDING
                            user.free_report_path = None
                            user.report_generation_error = "Отчет завис в процессе генерации"
                            logger.info(f"✅ Сброшен зависший бесплатный отчет для пользователя {telegram_id}")
                        
                        if user.premium_report_status == ReportGenerationStatus.PROCESSING:
                            user.premium_report_status = ReportGenerationStatus.PENDING
                            user.premium_report_path = None
                            user.report_generation_error = "Отчет завис в процессе генерации"
                            logger.info(f"✅ Сброшен зависший премиум отчет для пользователя {telegram_id}")
                        
                        await session.commit()
                        return True
                    else:
                        logger.info(f"📊 Отчет для пользователя {telegram_id} не считается зависшим (время: {time_diff})")
                else:
                    logger.info(f"📊 Нет времени начала генерации для пользователя {telegram_id}")
                
                return False
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Ошибка при сбросе зависших отчетов для пользователя {telegram_id}: {e}")
                raise e

# Создаем экземпляр сервиса
db_service = DatabaseService() 