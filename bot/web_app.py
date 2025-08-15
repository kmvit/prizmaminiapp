from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
from typing import Optional
from datetime import datetime
import decimal
import time

from bot.services.database_service import db_service
from bot.config import BASE_DIR, PERPLEXITY_ENABLED, settings
from bot.models.api_models import (
    AnswerRequest, UserProfileUpdate, CurrentQuestionResponse, 
    NextQuestionResponse, UserProgressResponse, UserProfileResponse,
    QuestionResponse, ProgressResponse, UserStatusResponse, ErrorResponse
)
from loguru import logger
from bot.services.oplata import RobokassaService
from bot.database.models import PaymentStatus, ReportGenerationStatus, User

# Путь к статическим файлам
STATIC_DIR = BASE_DIR / "frontend"

# Создаем FastAPI приложение
app = FastAPI(
    title="PRIZMA API",
    description="API для психологического тестирования с ИИ-анализом",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Сначала определяем все API маршруты, а потом статические файлы

# Вспомогательная функция для обновления текущего вопроса пользователя
async def update_user_current_question(telegram_id: int, question_id: int):
    """Обновить текущий вопрос пользователя"""
    from bot.database.database import async_session
    from bot.database.models import User
    from sqlalchemy import update as sql_update
    
    async with async_session() as session:
        stmt = sql_update(User).where(User.telegram_id == telegram_id).values(
            current_question_id=question_id,
            updated_at=datetime.utcnow()
        )
        await session.execute(stmt)
        await session.commit()

@app.get("/api/user/{telegram_id}/current-question", 
         response_model=CurrentQuestionResponse,
         summary="Получить текущий вопрос",
         description="Возвращает текущий вопрос для пользователя с информацией о прогрессе")
async def get_current_question(telegram_id: int):
    """Получить текущий вопрос для пользователя"""
    try:
        # Получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        # Если пользователь еще не начал тест, начинаем его
        if not user.current_question_id:
            # Для оплаченных пользователей проверяем, есть ли уже ответы
            if user.is_paid:
                answers = await db_service.get_user_answers(telegram_id)
                if answers:
                    # Если есть ответы, находим следующий вопрос после последнего отвеченного
                    # Получаем все вопросы, на которые пользователь ответил
                    answered_questions = []
                    for answer in answers:
                        question = await db_service.get_question(answer.question_id)
                        if question:
                            answered_questions.append(question)
                    
                    if answered_questions:
                        # Находим вопрос с максимальным order_number
                        last_question = max(answered_questions, key=lambda x: x.order_number)
                        
                        if last_question:
                            next_question = await db_service.get_next_question(last_question.id, user.is_paid)
                            if next_question:
                                # Обновляем текущий вопрос пользователя
                                await update_user_current_question(telegram_id, next_question.id)
                                user.current_question_id = next_question.id
                            else:
                                # Если следующего вопроса нет, тест завершен
                                user.test_completed = True
                                user.test_completed_at = datetime.utcnow()
                                # Обновляем пользователя через сервис
                                await db_service.complete_test(telegram_id)
                        else:
                            user = await db_service.start_test(telegram_id)
                else:
                    user = await db_service.start_test(telegram_id)
            else:
                user = await db_service.start_test(telegram_id)
        
        # Проверяем, завершен ли тест (только для бесплатных пользователей)
        if user.test_completed and not user.is_paid:
            logger.info(f"✅ Бесплатный тест для пользователя {telegram_id} уже завершен")
            raise HTTPException(status_code=400, detail="Test already completed")
        
        # Для премиум пользователей сбрасываем флаг завершения, если нужно продолжить
        if user.test_completed and user.is_paid:
            logger.info(f"🔄 Премиум пользователь {telegram_id} продолжает тест после оплаты")
            user.test_completed = False
            user.test_completed_at = None
            await db_service.update_user_test_status(telegram_id, False)
        
        # Получаем текущий вопрос
        question = await db_service.get_question(user.current_question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Получаем общее количество вопросов для этого пользователя
        total_questions = await db_service.get_total_questions(user.is_paid)
        
        # Получаем количество уже отвеченных вопросов
        answers = await db_service.get_user_answers(telegram_id)
        answered_count = len(answers)
        
        return CurrentQuestionResponse(
            question=QuestionResponse(
                id=question.id,
                text=question.text,
                order_number=question.order_number,
                type=question.type.value,
                allow_voice=question.allow_voice,
                max_length=question.max_length
            ),
            progress=ProgressResponse(
                current=question.order_number,
                total=total_questions,
                answered=answered_count
            ),
            user=UserStatusResponse(
                is_paid=user.is_paid,
                test_completed=user.test_completed
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting current question: {e}")
        raise HTTPException(status_code=500, detail="Failed to get question")

@app.post("/api/user/{telegram_id}/answer",
          response_model=NextQuestionResponse,
          summary="Сохранить ответ пользователя",
          description="Сохраняет ответ пользователя и возвращает следующий вопрос или завершает тест")
async def save_answer(telegram_id: int, answer_data: AnswerRequest):
    """Сохранить ответ пользователя и перейти к следующему вопросу"""
    try:
        logger.info(f"💬 Начало обработки ответа для пользователя {telegram_id}")
        
        # Получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        logger.info(f"👤 Пользователь: id={user.id}, is_paid={user.is_paid}, current_question_id={user.current_question_id}")
        
        if not user.current_question_id:
            logger.error(f"❌ Нет активного вопроса для пользователя {telegram_id}")
            raise HTTPException(status_code=400, detail="No active question")
        
        # Получаем текущий вопрос
        current_question = await db_service.get_question(user.current_question_id)
        
        if not current_question:
            raise HTTPException(status_code=404, detail="Current question not found")
        
        # Сохраняем ответ
        answer = await db_service.save_answer(
            telegram_id=telegram_id,
            question_id=current_question.id,
            text_answer=answer_data.text_answer,
            answer_type=answer_data.answer_type
        )
        
        # Perplexity анализ интегрирован только в генерацию отчетов, не в сохранение ответов
        # Сохраняем ответ без промежуточного анализа 
        logger.info(f"ℹ️ Ответ {answer.id} сохранен (ИИ-анализ будет выполнен при генерации отчета)")
        
        # Получаем следующий вопрос
        logger.info(f"🔍 Поиск следующего вопроса: current_order={current_question.order_number}, is_paid={user.is_paid}")
        next_question = await db_service.get_next_question(
            current_question.id,
            user.is_paid
        )
        logger.info(f"🎯 Результат поиска: {next_question.order_number if next_question else 'None'}")
        
        if next_question:
            # Обновляем текущий вопрос пользователя
            await update_user_current_question(telegram_id, next_question.id)
            
            # Получаем общее количество вопросов
            total_questions = await db_service.get_total_questions(user.is_paid)
            answers = await db_service.get_user_answers(telegram_id)
            answered_count = len(answers)
            
            return NextQuestionResponse(
                status="next_question",
                next_question=QuestionResponse(
                    id=next_question.id,
                    text=next_question.text,
                    order_number=next_question.order_number,
                    type=next_question.type.value,
                    allow_voice=next_question.allow_voice,
                    max_length=next_question.max_length
                ),
                progress=ProgressResponse(
                    current=next_question.order_number,
                    total=total_questions,
                    answered=answered_count
                )
            )
        else:
            # Тест завершен
            logger.info(f"✅ Завершение теста для пользователя {telegram_id} после вопроса {current_question.order_number}")
            await db_service.complete_test(telegram_id)
            
            # НЕ запускаем генерацию отчета в фоне - это будет делаться на loading.html
            # import asyncio
            # asyncio.create_task(generate_report_background(telegram_id))
            
            response_data = NextQuestionResponse(
                status="redirect_to_loading",  # Изменили статус для перенаправления на loading.html
                message="Поздравляем! Вы завершили тест. Генерируем персональный отчет..."
            )
            logger.info(f"📤 Отправляем ответ клиенту: {response_data.model_dump()}")
            return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to save answer")

@app.get("/api/user/{telegram_id}/progress",
         response_model=UserProgressResponse,
         summary="Получить прогресс пользователя",
         description="Возвращает информацию о прогрессе прохождения теста")
async def get_user_progress(telegram_id: int):
    """Получить прогресс пользователя"""
    try:
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        answers = await db_service.get_user_answers(telegram_id)
        total_questions = await db_service.get_total_questions(user.is_paid)
        
        return UserProgressResponse(
            user={
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "is_paid": user.is_paid,
                "test_completed": user.test_completed,
                "test_started_at": user.test_started_at.isoformat() if user.test_started_at else None,
                "test_completed_at": user.test_completed_at.isoformat() if user.test_completed_at else None
            },
            progress={
                "answered": len(answers),
                "total": total_questions,
                "percentage": round((len(answers) / total_questions) * 100, 1) if total_questions > 0 else 0
            },
            answers=[
                {
                    "question_id": ans.question_id,
                    "text_answer": ans.text_answer,
                    "ai_analysis": ans.ai_analysis,
                    "created_at": ans.created_at.isoformat()
                }
                for ans in answers
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress")

@app.get("/api/user/{telegram_id}/profile",
         response_model=UserProfileResponse,
         summary="Получить профиль пользователя",
         description="Возвращает информацию профиля пользователя")
async def get_user_profile(telegram_id: int):
    """Получить профиль пользователя"""
    try:
        logger.info(f"Получен запрос на получение профиля для telegram_id: {telegram_id}")
        
        # Получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        logger.info(f"Пользователь найден: {user.telegram_id}")
        
        # Определяем статус оплаты
        payment_status = None
        if user.is_paid:
            payment_status = "completed"
        elif user.is_premium_paid:
            payment_status = "pending"
        
        return UserProfileResponse(
            status="success",
            user={
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "name": user.name,
                "age": user.age,
                "gender": user.gender
            },
            payment_status=payment_status
        )
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

@app.post("/api/user/{telegram_id}/profile",
          response_model=UserProfileResponse,
          summary="Обновить профиль пользователя",
          description="Обновляет информацию профиля пользователя")
async def update_user_profile(telegram_id: int, profile_data: UserProfileUpdate):
    """Обновить профиль пользователя"""
    try:
        logger.info(f"Получен запрос на обновление профиля для telegram_id: {telegram_id}")
        logger.info(f"Данные профиля: {profile_data}")
        
        # Сначала создаем или получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        logger.info(f"Пользователь получен/создан: {user.telegram_id}")
        
        # Затем обновляем профиль
        user = await db_service.update_user_profile(
            telegram_id=telegram_id,
            name=profile_data.name,
            age=profile_data.age,
            gender=profile_data.gender
        )
        logger.info(f"Профиль обновлен: name={user.name}, age={user.age}, gender={user.gender}")
        
        # Определяем статус оплаты
        payment_status = None
        if user.is_paid:
            payment_status = "completed"
        elif user.is_premium_paid:
            payment_status = "pending"
        
        return UserProfileResponse(
            status="success",
            user={
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "name": user.name,
                "age": user.age,
                "gender": user.gender
            },
            payment_status=payment_status
        )
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

# Обработчик ошибок
from fastapi.responses import JSONResponse, RedirectResponse

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

# Информационные эндпоинты
@app.get("/api/health", summary="Проверка работоспособности API")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok", "message": "PRIZMA API is running"}

@app.get("/api/info", summary="Информация об API")
async def api_info():
    """Информация об API"""
    return {
        "name": "PRIZMA API",
        "version": "1.0.0",
        "description": "API для психологического тестирования с ИИ-анализом",
        "features": {
            "perplexity_ai": PERPLEXITY_ENABLED,
            "pdf_generation": True,
            "payments": True
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/health"
        }
    }

@app.get("/api/user/{telegram_id}/report-status", summary="Проверить статус генерации отчета")
async def check_report_status(telegram_id: int):
    """Проверить готовность отчета пользователя"""
    try:
        # Проверяем, что пользователь завершил тест
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {"status": "test_not_completed", "message": "Тест не завершен"}
        
        # Проверяем, не оплатил ли пользователь премиум отчет
        if user.is_paid:
            logger.info(f"💰 Пользователь {telegram_id} оплатил премиум отчет. Не возвращаем статус бесплатного отчета.")
            return {"status": "premium_paid", "message": "Для оплативших премиум пользователей используется премиум отчет."}
        
        # Ищем последний отчет пользователя
        reports_dir = Path("reports")
        pattern = f"prizma_report_{telegram_id}_*.pdf"
        
        import glob
        report_files = glob.glob(str(reports_dir / pattern))
        
        if report_files:
            # Сортируем по timestamp в имени файла (более надежно чем st_mtime)
            # Имя файла: prizma_report_{telegram_id}_{timestamp}.pdf
            def extract_timestamp(filepath):
                filename = Path(filepath).name
                # Извлекаем timestamp из имени файла: prizma_report_123456789_20250627_082506.pdf
                parts = filename.split('_')
                if len(parts) >= 5:
                    try:
                        # Берем дату и время: parts[3] = '20250627', parts[4] = '082506.pdf'
                        date_part = parts[3]
                        time_part = parts[4].replace('.pdf', '').replace('.txt', '')
                        timestamp_str = f"{date_part}_{time_part}"
                        return timestamp_str
                    except:
                        return "00000000_000000"
                return "00000000_000000"
                
            # Находим последний файл по timestamp
            latest_report = max(report_files, key=extract_timestamp)
            return {"status": "ready", "message": "Отчет готов к скачиванию", "report_path": latest_report}
        else:
            return {"status": "not_ready", "message": "Отчет еще не готов"}
            
    except Exception as e:
        logger.error(f"Error checking report status: {e}")
        return {"status": "error", "message": "Ошибка при проверке статуса отчета"}

@app.post("/api/user/{telegram_id}/generate-report", summary="Запустить генерацию отчета")
async def start_report_generation(telegram_id: int):
    """Запустить генерацию отчета пользователя"""
    try:
        # Проверяем, что пользователь завершил тест
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {"status": "error", "message": "Тест не завершен"}
        
        # Проверяем, не оплатил ли пользователь премиум отчет
        if user.is_paid:
            logger.warning(f"⚠️ Пользователь {telegram_id} оплатил премиум отчет. Не запускаем бесплатную генерацию.")
            return {"status": "premium_paid", "message": "Для оплативших премиум пользователей используется премиум отчет."}
        
        logger.info(f"🚀 Запускаем синхронную генерацию БЕСПЛАТНОГО отчета для пользователя {telegram_id}")
        
        # Запускаем синхронную генерацию отчета
        report_path = await generate_report_background(telegram_id)
        
        if report_path:
            return {"status": "success", "message": "Отчет успешно сгенерирован", "report_path": report_path}
        else:
            return {"status": "error", "message": "Ошибка при генерации отчета"}
            
    except Exception as e:
        logger.error(f"Error starting report generation: {e}")
        return {"status": "error", "message": f"Ошибка при генерации отчета: {str(e)}"}

@app.get("/api/download/report/{telegram_id}", summary="Скачать персональный отчет")
async def download_personal_report(telegram_id: int, download: Optional[str] = None, method: Optional[str] = None, t: Optional[str] = None):
    """Скачать готовый персональный отчет пользователя"""
    from fastapi.responses import FileResponse
    import os
    import glob
    
    try:
        logger.info(f"📁 Запрос скачивания отчета для пользователя {telegram_id}")
        logger.info(f"📊 Параметры: download={download}, method={method}, t={t}")
        
        # Проверяем, что пользователь завершил тест
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            logger.warning(f"⚠️ Пользователь {telegram_id} не завершил тест")
            raise HTTPException(status_code=400, detail="Тест не завершен. Завершите тест для получения отчета.")
        
        # Проверяем, не оплатил ли пользователь премиум отчет
        if user.is_paid:
            logger.info(f"💰 Пользователь {telegram_id} оплатил премиум отчет. Перенаправляем на премиум отчет.")
            # Перенаправляем на премиум отчет
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=f"/api/download/premium-report/{telegram_id}")
        
        # Ищем готовый отчет пользователя
        reports_dir = Path("reports")
        pattern = f"prizma_report_{telegram_id}_*.pdf"
        report_files = glob.glob(str(reports_dir / pattern))
        
        if not report_files:
            logger.warning(f"⚠️ Отчет для пользователя {telegram_id} не найден, запускаем генерацию...")
            
            # Запускаем генерацию отчета и ждем завершения
            try:
                await generate_report_background(telegram_id)
                
                # Повторно ищем отчет после генерации
                report_files = glob.glob(str(reports_dir / pattern))
                if not report_files:
                    logger.error(f"❌ Отчет не создался даже после генерации для пользователя {telegram_id}")
                    raise HTTPException(status_code=500, detail="Ошибка создания отчета. Попробуйте позже.")
                
                logger.info(f"✅ Отчет успешно создан для пользователя {telegram_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка при генерации отчета для пользователя {telegram_id}: {e}")
                raise HTTPException(status_code=500, detail="Ошибка создания отчета. Попробуйте позже.")
        
        # Функция для извлечения timestamp из имени файла
        def extract_timestamp(filepath):
            filename = Path(filepath).name
            # Извлекаем timestamp из имени файла: prizma_report_123456789_20250627_082506.pdf
            parts = filename.split('_')
            if len(parts) >= 5:
                try:
                    # Берем дату и время: parts[3] = '20250627', parts[4] = '082506.pdf'
                    date_part = parts[3]
                    time_part = parts[4].replace('.pdf', '').replace('.txt', '')
                    timestamp_str = f"{date_part}_{time_part}"
                    return timestamp_str
                except:
                    pass
            # Если не удается извлечь timestamp, используем время модификации как fallback
            return str(int(Path(filepath).stat().st_mtime))
        
        # Сортируем по timestamp (последний будет первым) и берем последний отчет
        report_files.sort(key=extract_timestamp, reverse=True)
        latest_report = report_files[0]
        
        logger.info(f"📋 Найдено отчетов: {len(report_files)}")
        logger.info(f"📄 Выбран последний отчет: {latest_report}")
        for i, report in enumerate(report_files[:3]):  # Показываем первые 3 для отладки
            logger.info(f"   {i+1}. {Path(report).name} (timestamp: {extract_timestamp(report)})")
        
        if not os.path.exists(latest_report):
            logger.error(f"❌ Файл отчета не найден: {latest_report}")
            raise HTTPException(status_code=500, detail="Файл отчета поврежден")
        
        logger.info(f"📄 Отдаем готовый отчет: {latest_report}, размер: {os.path.getsize(latest_report)} байт")
        
        # Определяем заголовки для скачивания
        headers = {}
        
        # Для принудительного скачивания (из Telegram Web App)
        if download == "1":
            headers["Content-Disposition"] = f'attachment; filename="prizma-report-{telegram_id}.pdf"'
            headers["Content-Type"] = "application/pdf"
            headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            headers["Pragma"] = "no-cache"
            headers["Expires"] = "0"
            logger.info("📱 Принудительное скачивание для Telegram Web App")
        else:
            # Обычное открытие в браузере
            headers["Content-Disposition"] = f'inline; filename="prizma-report-{telegram_id}.pdf"'
            logger.info("🌐 Обычное открытие в браузере")
        
        # Возвращаем файл для скачивания
        return FileResponse(
            path=latest_report,
            media_type='application/pdf',
            filename=f"prizma-report-{telegram_id}.pdf",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading report: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при скачивании отчета")

# Функция фоновой генерации отчета
async def generate_report_background(telegram_id: int):
    """Генерация отчета в фоновом режиме после завершения теста"""
    try:
        logger.info(f"🔄 Начинаем фоновую генерацию отчета для пользователя {telegram_id}")
        
        # Получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        # Получаем ответы и вопросы
        answers = await db_service.get_user_answers(telegram_id)
        questions = await db_service.get_questions()
        
        # Генерируем отчет через AI сервис
        from bot.services.perplexity import AIAnalysisService
        ai_service = AIAnalysisService()
        
        result = await ai_service.generate_psychological_report(user, questions, answers)
        
        if result.get("success"):
            report_path = result['report_file']
            logger.info(f"✅ Фоновая генерация отчета завершена успешно для пользователя {telegram_id}: {report_path}")
            
            # НЕ удаляем данные пользователя - оставляем их для возможного повторного прохождения
            
            # Отправляем уведомление в Telegram
            from bot.services.telegram_service import telegram_service
            await telegram_service.send_report_ready_notification(
                telegram_id=telegram_id,
                report_path=report_path,
                is_premium=False
            )
            
            return report_path
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            logger.error(f"❌ Ошибка фоновой генерации отчета для пользователя {telegram_id}: {error_msg}")
            
            # Отправляем уведомление об ошибке в Telegram
            from bot.services.telegram_service import telegram_service
            await telegram_service.send_error_notification(
                telegram_id=telegram_id,
                error_message=error_msg
            )
            
            return None
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка фоновой генерации отчета для пользователя {telegram_id}: {e}")
        
        # Отправляем уведомление об ошибке в Telegram
        from bot.services.telegram_service import telegram_service
        await telegram_service.send_error_notification(
            telegram_id=telegram_id,
            error_message=str(e)
        )
        
        return None

# ПЛАТНАЯ ВЕРСИЯ - новые эндпоинты

@app.get("/api/user/{telegram_id}/premium-report-status", summary="Проверить статус генерации платного отчета")
async def check_premium_report_status(telegram_id: int):
    """Проверить статус готовности платного отчета пользователя"""
    try:
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {"status": "test_not_completed", "message": "Тест не завершен"}
        
        # Проверяем, оплатил ли пользователь премиум отчет
        if not user.is_paid:
            return {"status": "payment_required", "message": "Для доступа к премиум отчету требуется оплата."}
        
        # Получаем статус генерации из БД
        status_info = await db_service.get_report_generation_status(telegram_id, "premium")
        
        if status_info.get("status") == "completed" and status_info.get("report_path"):
            return {
                "status": "ready", 
                "message": "Премиум отчет готов к скачиванию", 
                "report_path": status_info["report_path"]
            }
        elif status_info.get("status") == "processing":
            return {"status": "processing", "message": "Отчет генерируется..."}
        elif status_info.get("status") == "failed":
            return {
                "status": "failed", 
                "message": "Ошибка генерации отчета", 
                "error": status_info.get("error", "Неизвестная ошибка")
            }
        else:
            return {"status": "not_started", "message": "Генерация не запущена"}
            
    except Exception as e:
        logger.error(f"Error checking premium report status: {e}")
        return {"status": "error", "message": "Ошибка при проверке статуса платного отчета"}

@app.post("/api/user/{telegram_id}/reset-test", summary="Сбросить тест пользователя")
async def reset_user_test(telegram_id: int):
    """Сбросить тест пользователя для повторного прохождения"""
    try:
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        # Сбрасываем статус теста
        user.test_completed = False
        user.test_completed_at = None
        user.current_question_id = None
        user.test_started_at = None
        
        # Удаляем все ответы пользователя
        deleted_count = await db_service.clear_user_answers(telegram_id)
        
        logger.info(f"🔄 Тест сброшен для пользователя {telegram_id}, удалено {deleted_count} ответов")
        
        return {"status": "success", "message": "Тест сброшен", "deleted_answers": deleted_count}
        
    except Exception as e:
        logger.error(f"Error resetting test: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset test")

@app.post("/api/user/{telegram_id}/start-premium-payment", summary="Начать процесс оплаты премиум отчета")
async def start_premium_payment(telegram_id: int):
    try:
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if user.is_paid:
            return {"status": "already_paid", "message": "Вы уже оплатили премиум отчет."}

        # Сумма оплаты (например, 1000 рублей)
        amount_decimal = decimal.Decimal(1.00) # Ваша цена за премиум отчет
        amount_in_kopecks = int(amount_decimal * 100) # Преобразуем в копейки (целое число)
        description = f"Оплата премиум отчета для пользователя {telegram_id}"

        # 1. Сначала создаем запись о платеже (invoice_id временно уникальный timestamp)
        temp_invoice_id = str(int(time.time() * 1_000_000))
        payment = await db_service.create_payment(
            user_id=user.id,
            amount=amount_in_kopecks,
            currency="RUB",
            description=description,
            invoice_id=temp_invoice_id,
            status=PaymentStatus.PENDING
        )

        # 2. Получаем автоинкрементный ID платежа
        inv_id = payment.id

        # 3. Обновляем invoice_id в базе (если нужно)
        await db_service.update_payment_invoice_id(payment.id, str(inv_id))

        robokassa = RobokassaService(
            merchant_login=settings.ROBOKASSA_LOGIN,
            merchant_password_1=settings.ROBOKASSA_PASSWORD_1,
            merchant_password_2=settings.ROBOKASSA_PASSWORD_2,
            is_test=1 if settings.ROBOKASSA_TEST else 0
        )

        # 4. Формируем URL для возврата в Telegram Web App
        base_url = settings.WEBAPP_URL
        
        # URL для успешного платежа - возвращаем в Telegram Web App с параметром успеха
        telegram_success_url = f"{settings.TELEGRAM_WEBAPP_URL}?startapp=payment_success_{inv_id}"
        success_url = telegram_success_url
        
        # URL для неуспешного платежа - возвращаем в Telegram Web App с параметром ошибки
        telegram_fail_url = f"{settings.TELEGRAM_WEBAPP_URL}?startapp=payment_fail"
        fail_url = telegram_fail_url
        
        logger.info(f"🔗 SuccessURL: {success_url}")
        logger.info(f"🔗 FailURL: {fail_url}")

        # 5. Генерируем ссылку Robokassa с URL возврата
        payment_link = robokassa.generate_payment_link(
            cost=amount_decimal,
            number=inv_id,
            description=description,
            is_test=1 if settings.ROBOKASSA_TEST else 0,
            success_url=success_url,
            fail_url=fail_url
        )
        
        logger.info(f"💰 Сгенерирована платежная ссылка для пользователя {telegram_id}: {payment_link}")
        
        return {"status": "success", "message": "Платежная ссылка сгенерирована", "payment_link": payment_link}
        
    except Exception as e:
        logger.error(f"Error starting premium payment for user {telegram_id}: {e}")
        return {"status": "error", "message": f"Ошибка при инициализации платежа: {str(e)}"}

@app.get("/api/payment/fail-redirect", summary="Обработка неудачной оплаты и редирект")
async def handle_payment_fail(request: Request):
    """Перенаправляет пользователя обратно в Web App в случае неудачной оплаты."""
    try:
        telegram_webapp_url = f"{settings.TELEGRAM_WEBAPP_URL}?startapp=payment_fail"
        logger.info(f"❌ Неудачная оплата. Перенаправляем на: {telegram_webapp_url}")
        return RedirectResponse(url=telegram_webapp_url, status_code=302)
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке неудачной оплаты: {e}")
        # В крайнем случае, можно перенаправить на статичную страницу ошибки
        return RedirectResponse(url="/uncomplete-payment.html", status_code=302)

@app.get("/api/payment/success/{invoice_id}", summary="Обработка успешной оплаты и редирект")
async def handle_payment_success(invoice_id: int, request: Request):
    """
    Этот эндпоинт принимает редирект от Robokassa, проверяет платеж
    и перенаправляет пользователя обратно в Telegram Web App.
    """
    try:
        # Проверяем подлинность запроса от Robokassa (опционально, но рекомендуется)
        # ... (здесь можно добавить логику проверки подписи, если Robokassa ее присылает)
        
        # Находим платеж по invoice_id
        payment = await db_service.get_payment_by_invoice_id(invoice_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Платеж не найден")
            
        # Обновляем статус, если нужно
        if payment.status != PaymentStatus.COMPLETED:
            await db_service.update_payment_status(payment.id, PaymentStatus.COMPLETED)
            user = await db_service.get_user_by_id(payment.user_id)
            if user:
                await db_service.upgrade_to_premium_and_continue_test(user.telegram_id)

        # Формируем URL для возврата в Web App
        telegram_webapp_url = f"{settings.TELEGRAM_WEBAPP_URL}?startapp=payment_success"
        
        logger.info(f"✅ Успешная оплата. Перенаправляем на: {telegram_webapp_url}")
        
        return RedirectResponse(url=telegram_webapp_url, status_code=302)

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке успешной оплаты: {e}")
        # В случае ошибки, перенаправляем на страницу ошибки
        fail_url = f"{settings.TELEGRAM_WEBAPP_URL}?startapp=payment_fail"
        return RedirectResponse(url=fail_url, status_code=302)

@app.get("/api/robokassa/result", summary="Endpoint для ResultURL Robokassa")
async def robokassa_result(request: Request):
    try:
        query_params = dict(request.query_params)
        logger.info(f"🔔 Получено уведомление ResultURL от Robokassa: {query_params}")
        out_sum = query_params.get('OutSum')
        inv_id = query_params.get('InvId')
        signature_value = query_params.get('SignatureValue')
        if not all([out_sum, inv_id, signature_value]):
            logger.warning("⚠️ Недостаточно параметров в ResultURL")
            return "bad sign"
        robokassa = RobokassaService(
            merchant_login=settings.ROBOKASSA_LOGIN,
            merchant_password_1=settings.ROBOKASSA_PASSWORD_1,
            merchant_password_2=settings.ROBOKASSA_PASSWORD_2,
            is_test=1 if settings.ROBOKASSA_TEST else 0
        )
        # Проверяем подпись для ResultURL
        logger.info(f"🔍 Проверка подписи ResultURL: out_sum={out_sum}, inv_id={inv_id}, signature_value={signature_value}")
        signature_valid = robokassa.check_signature_result(out_sum, inv_id, signature_value)
        logger.info(f"🔍 Результат проверки подписи: {signature_valid}")
        if not signature_valid:
            logger.warning(f"❌ Неверная подпись в ResultURL для InvId: {inv_id}")
            return "bad sign"

        # Обновляем статус платежа в БД
        payment = await db_service.get_payment_by_invoice_id(inv_id)
        if payment:
            logger.info(f"💰 Найден платеж в БД: ID={payment.id}, статус={payment.status}, пользователь={payment.user_id}")
            
            # Проверяем, не обработан ли уже платеж
            if payment.status == PaymentStatus.COMPLETED:
                logger.info(f"✅ Платеж {inv_id} уже обработан (статус COMPLETED)")
                return f"OK{inv_id}"
            
            # Обновляем статус платежа
            await db_service.update_payment_status(payment.id, PaymentStatus.COMPLETED)
            user = await db_service.get_user_by_id(payment.user_id)
            if user:
                await db_service.upgrade_to_premium_and_continue_test(user.telegram_id)
                logger.info(f"✅ Платеж {inv_id} успешно завершен для пользователя {user.telegram_id}, тест продолжен")
            else:
                logger.error(f"❌ Пользователь с ID {payment.user_id} не найден")
            return f"OK{inv_id}"
        else:
            logger.warning(f"⚠️ Платеж с InvId {inv_id} не найден в БД")
            return "bad sign"

    except Exception as e:
        logger.error(f"❌ Ошибка обработки ResultURL Robokassa: {e}")
        return "error"

# Кэш для отслеживания обработанных SuccessURL запросов
_processed_success_requests = set()
_last_cache_cleanup = time.time()

def cleanup_success_cache():
    """Очищаем кэш обработанных запросов каждые 24 часа"""
    global _last_cache_cleanup, _processed_success_requests
    current_time = time.time()
    if current_time - _last_cache_cleanup > 86400:  # 24 часа
        _processed_success_requests.clear()
        _last_cache_cleanup = current_time
        logger.info("🧹 Кэш обработанных SuccessURL запросов очищен")

@app.get("/api/robokassa/success", summary="Endpoint для SuccessURL Robokassa")
async def robokassa_success(request: Request):
    try:
        # Очищаем кэш при необходимости
        cleanup_success_cache()
        
        query_params = dict(request.query_params)
        out_sum = query_params.get('OutSum')
        inv_id = query_params.get('InvId')
        signature_value = query_params.get('SignatureValue')
        
        # Создаем уникальный ключ для запроса
        request_key = f"{inv_id}_{out_sum}_{signature_value}"
        
        # Проверяем, не обрабатывали ли мы уже этот запрос
        if request_key in _processed_success_requests:
            logger.info(f"🔄 Дублирующий запрос SuccessURL для InvId {inv_id}, пропускаем")
            response = RedirectResponse(url="/api/payment/success", status_code=302)
            # Добавляем заголовки для предотвращения кэширования
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        
        logger.info(f"✅ Получено уведомление SuccessURL от Robokassa: {query_params}")
        
        if not all([out_sum, inv_id, signature_value]):
            logger.warning("⚠️ Недостаточно параметров в SuccessURL")
            return RedirectResponse(url="/uncomplete-payment.html", status_code=302)
        
        robokassa = RobokassaService(
            merchant_login=settings.ROBOKASSA_LOGIN,
            merchant_password_1=settings.ROBOKASSA_PASSWORD_1,
            merchant_password_2=settings.ROBOKASSA_PASSWORD_2,
            is_test=1 if settings.ROBOKASSA_TEST else 0
        )
        
        # Проверяем подпись для SuccessURL
        if not robokassa.check_signature_success(out_sum, inv_id, signature_value):
            logger.warning(f"❌ Неверная подпись в SuccessURL для InvId: {inv_id}")
            return RedirectResponse(url="/uncomplete-payment.html", status_code=302)

        # Проверяем статус платежа в БД
        payment = await db_service.get_payment_by_invoice_id(inv_id)
        if payment:
            logger.info(f"💰 Найден платеж в БД: ID={payment.id}, статус={payment.status}, пользователь={payment.user_id}")
            
            if payment.status == PaymentStatus.COMPLETED:
                logger.info(f"🎉 Платеж {inv_id} уже подтвержден. Перенаправляем на страницу успеха.")
                # Добавляем запрос в кэш обработанных
                _processed_success_requests.add(request_key)
                # Перенаправляем на страницу успешного платежа
                logger.info(f"🔄 Перенаправление на /complete-payment.html")
                response = RedirectResponse(url="/complete-payment.html", status_code=302)
                # Добавляем заголовки для предотвращения кэширования
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            else:
                logger.warning(f"⚠️ Платеж {inv_id} найден, но статус не COMPLETED: {payment.status}")
                # Попробуем обновить статус на COMPLETED (на случай если ResultURL не сработал)
                await db_service.update_payment_status(payment.id, PaymentStatus.COMPLETED)
                user = await db_service.get_user_by_id(payment.user_id)
                if user:
                    logger.info(f"👤 Найден пользователь: ID={user.id}, telegram_id={user.telegram_id}, is_paid={user.is_paid}")
                    await db_service.upgrade_to_paid(user.telegram_id)
                    logger.info(f"✅ Платеж {inv_id} обновлен до COMPLETED для пользователя {user.telegram_id}")
                    # Проверяем, что статус обновился
                    updated_user = await db_service.get_user_by_id(payment.user_id)
                    logger.info(f"✅ Статус пользователя после обновления: is_paid={updated_user.is_paid}")
                else:
                    logger.error(f"❌ Пользователь с ID {payment.user_id} не найден")
                
                # Добавляем запрос в кэш обработанных
                _processed_success_requests.add(request_key)
                # Перенаправляем на страницу успешного платежа через API endpoint
                logger.info(f"🔄 Перенаправляем пользователя на страницу успешного платежа")
                response = RedirectResponse(url="/api/payment/success", status_code=302)
                # Добавляем заголовки для предотвращения кэширования
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        else:
            logger.warning(f"⚠️ Платеж с InvId {inv_id} не найден в БД")
            logger.error(f"❌ Перенаправление на страницу неудачного платежа из-за отсутствия платежа в БД")
            return RedirectResponse(url="/uncomplete-payment.html", status_code=302)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки SuccessURL Robokassa: {e}")
        return RedirectResponse(url="/uncomplete-payment.html", status_code=302)


@app.get("/api/robokassa/fail", summary="Endpoint для FailURL Robokassa")
async def robokassa_fail(request: Request):
    logger.info(f"💔 Получено уведомление FailURL от Robokassa: {request.query_params}")
    return RedirectResponse(url="/uncomplete-payment.html", status_code=302)

@app.get("/api/payment/redirect-fail", summary="Redirect для неуспешного платежа (настройки Робокассы)")
async def payment_redirect_fail(request: Request):
    """Эндпоинт для редиректа при неуспешной оплате, настроенный в Робокассе"""
    logger.info(f"💔 Редирект неуспешного платежа: {request.query_params}")
    return RedirectResponse(url="/uncomplete-payment.html", status_code=302)




@app.get("/api/payment/success/{inv_id}", summary="Успешная оплата с ID")
async def payment_success_with_id(inv_id: str, request: Request):
    """Обработка успешной оплаты с ID платежа (генерируется в коде)"""
    logger.info(f"✅ Успешная оплата с InvId: {inv_id}, параметры: {request.query_params}")
    # Перенаправляем на общую страницу успеха
    return RedirectResponse(url="/api/payment/success", status_code=302)

@app.get("/api/payment/success", summary="Страница успешной оплаты для Telegram Web App")
async def payment_success_page(request: Request):
    """Специальная страница для отображения успешной оплаты в Telegram Web App"""
    try:
        # Читаем HTML файл
        html_file = STATIC_DIR / "complete-payment.html"
        if not html_file.exists():
            raise HTTPException(status_code=404, detail="Страница не найдена")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Возвращаем HTML с правильными заголовками для Telegram Web App
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content=html_content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке страницы успешной оплаты: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки страницы")


@app.post("/api/user/{telegram_id}/generate-premium-report", summary="Запустить генерацию платного отчета")
async def start_premium_report_generation(telegram_id: int, background_tasks: BackgroundTasks):
    """Запустить асинхронную генерацию платного отчета пользователя (50 вопросов)"""
    try:
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {"status": "error", "message": "Тест не завершен"}
        
        # Проверяем, оплатил ли пользователь премиум отчет
        if not user.is_paid:
            logger.warning(f"⚠️ Пользователь {telegram_id} не оплатил премиум отчет. Перенаправляем на оплату.")
            return {"status": "payment_required", "message": "Для генерации премиум отчета требуется оплата."}

        # Проверяем и сбрасываем зависшие отчеты
        await db_service.reset_stuck_reports(telegram_id)
        
        # Проверяем, не генерируется ли уже отчет
        is_generating = await db_service.is_report_generating(telegram_id, "premium")
        logger.info(f"🔍 Проверка генерации премиум отчета для пользователя {telegram_id}: {is_generating}")
        
        if is_generating:
            logger.info(f"⏳ Отчет уже генерируется для пользователя {telegram_id}")
            # Дополнительно возвращаем ссылку на бота, чтобы фронт мог открыть бот с сообщением
            bot_link = os.getenv("TELEGRAM_BOT_LINK", "https://t.me/myprizma_bot")
            return {
                "status": "already_processing",
                "message": "Ваш премиум-отчет уже генерируется. Мы пришлем его в бот, как будет готов.",
                "bot_link": bot_link
            }

        # Обновляем статус в БД
        await db_service.update_report_generation_status(
            telegram_id, 
            "premium", 
            ReportGenerationStatus.PROCESSING
        )
        
        # Запускаем фоновую задачу
        background_tasks.add_task(generate_premium_report_async, telegram_id)
        
        logger.info(f"🚀 Запущена асинхронная генерация ПЛАТНОГО отчета для пользователя {telegram_id}")
        
        return {
            "status": "started", 
            "message": "Генерация премиум отчета запущена. Вы получите уведомление по готовности."
        }
            
    except Exception as e:
        logger.error(f"Error starting premium report generation: {e}")
        return {"status": "error", "message": f"Ошибка при запуске генерации отчета: {str(e)}"}

@app.get("/api/download/premium-report/{telegram_id}", summary="Скачать платный персональный отчет")
async def download_premium_personal_report(telegram_id: int, download: Optional[str] = None, method: Optional[str] = None, t: Optional[str] = None):
    """Скачать готовый платный персональный отчет пользователя (50 вопросов)"""
    from fastapi.responses import FileResponse
    import os
    import glob
    
    try:
        logger.info(f"📁 Запрос скачивания ПЛАТНОГО отчета для пользователя {telegram_id}")
        logger.info(f"📊 Параметры: download={download}, method={method}, t={t}")
        
        # Получаем пользователя (для проверки оплаты)
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        # Ищем готовый платный отчет пользователя (если файл уже есть — разрешаем скачивание независимо от статуса is_paid)
        reports_dir = Path("reports")
        pattern = f"prizma_premium_report_{telegram_id}_*.pdf"
        report_files = glob.glob(str(reports_dir / pattern))
        
        if not report_files:
            # Если файла нет, проверяем оплату
            if not user.is_paid:
                logger.warning(f"⚠️ Пользователь {telegram_id} не оплатил премиум отчет и файл не найден")
                raise HTTPException(status_code=403, detail="Для доступа к премиум отчету требуется оплата.")
            
            logger.warning(f"⚠️ Платный отчет для пользователя {telegram_id} не найден, запускаем генерацию...")
            
            # Запускаем генерацию платного отчета и ждем завершения
            try:
                await generate_premium_report_background(telegram_id)
                
                # Повторно ищем отчет после генерации
                report_files = glob.glob(str(reports_dir / pattern))
                if not report_files:
                    logger.error(f"❌ Платный отчет не создался даже после генерации для пользователя {telegram_id}")
                    raise HTTPException(status_code=500, detail="Ошибка создания платного отчета. Попробуйте позже.")
                
                logger.info(f"✅ Платный отчет успешно создан для пользователя {telegram_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка при генерации платного отчета для пользователя {telegram_id}: {e}")
                raise HTTPException(status_code=500, detail="Ошибка создания платного отчета. Попробуйте позже.")
        
        # Функция для извлечения timestamp из имени файла
        def extract_timestamp(filepath):
            filename = Path(filepath).name
            parts = filename.split('_')
            if len(parts) >= 5:
                try:
                    date_part = parts[3]
                    time_part = parts[4].replace('.pdf', '').replace('.txt', '')
                    timestamp_str = f"{date_part}_{time_part}"
                    return timestamp_str
                except:
                    pass
            return str(int(Path(filepath).stat().st_mtime))
        
        # Сортируем по timestamp и берем последний отчет
        report_files.sort(key=extract_timestamp, reverse=True)
        latest_report = report_files[0]
        
        logger.info(f"📋 Найдено платных отчетов: {len(report_files)}")
        logger.info(f"📄 Выбран последний платный отчет: {latest_report}")
        
        if not os.path.exists(latest_report):
            logger.error(f"❌ Файл платного отчета не найден: {latest_report}")
            raise HTTPException(status_code=500, detail="Файл платного отчета поврежден")
        
        logger.info(f"📄 Отдаем готовый платный отчет: {latest_report}, размер: {os.path.getsize(latest_report)} байт")
        
        # Определяем заголовки для скачивания
        headers = {}
        
        # Для принудительного скачивания (из Telegram Web App)
        if download == "1":
            headers["Content-Disposition"] = f'attachment; filename="prizma-premium-report-{telegram_id}.pdf"'
            headers["Content-Type"] = "application/pdf"
            headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            headers["Pragma"] = "no-cache"
            headers["Expires"] = "0"
            logger.info("📱 Принудительное скачивание платного отчета для Telegram Web App")
        else:
            # Обычное открытие в браузере
            headers["Content-Disposition"] = f'inline; filename="prizma-premium-report-{telegram_id}.pdf"'
            logger.info("🌐 Обычное открытие платного отчета в браузере")
        
        # Возвращаем файл для скачивания
        return FileResponse(
            path=latest_report,
            media_type='application/pdf',
            filename=f"prizma-premium-report-{telegram_id}.pdf",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading premium report: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при скачивании платного отчета")

# Функция фоновой генерации платного отчета (синхронная версия для обратной совместимости)
async def generate_premium_report_background(telegram_id: int):
    """Генерация платного отчета в фоновом режиме после завершения теста (50 вопросов)"""
    try:
        logger.info(f"🔄 Начинаем фоновую генерацию ПЛАТНОГО отчета для пользователя {telegram_id}")
        
        # Получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        # Получаем ответы и вопросы
        answers = await db_service.get_user_answers(telegram_id)
        questions = await db_service.get_questions()
        
        # Генерируем платный отчет через AI сервис
        from bot.services.perplexity import AIAnalysisService
        ai_service = AIAnalysisService()
        
        result = await ai_service.generate_premium_report(user, questions, answers)
        
        if result.get("success"):
            report_path = result['report_file']
            logger.info(f"✅ Фоновая генерация ПЛАТНОГО отчета завершена успешно для пользователя {telegram_id}: {report_path}")
            return report_path
        else:
            logger.error(f"❌ Ошибка фоновой генерации ПЛАТНОГО отчета для пользователя {telegram_id}: {result.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка фоновой генерации ПЛАТНОГО отчета для пользователя {telegram_id}: {e}")
        return None

# Асинхронная функция генерации отчета для Background Tasks
async def generate_premium_report_async(telegram_id: int):
    """Асинхронная генерация премиум отчета в фоновом режиме"""
    try:
        logger.info(f"🔄 Начинаем асинхронную генерацию ПЛАТНОГО отчета для пользователя {telegram_id}")
        
        # Получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        # Получаем ответы и вопросы
        answers = await db_service.get_user_answers(telegram_id)
        questions = await db_service.get_questions()
        
        # Генерируем платный отчет через AI сервис
        from bot.services.perplexity import AIAnalysisService
        ai_service = AIAnalysisService()
        
        result = await ai_service.generate_premium_report(user, questions, answers)
        
        if result.get("success"):
            report_path = result['report_file']
            
            # Обновляем статус в БД
            await db_service.update_report_generation_status(
                telegram_id, 
                "premium", 
                ReportGenerationStatus.COMPLETED, 
                report_path=report_path
            )
            
            logger.info(f"✅ Асинхронная генерация ПЛАТНОГО отчета завершена успешно для пользователя {telegram_id}: {report_path}")
            
            # Отправляем уведомление в Telegram
            from bot.services.telegram_service import telegram_service
            sent = await telegram_service.send_report_ready_notification(
                telegram_id=telegram_id,
                report_path=report_path,
                is_premium=True
            )
            # Если успешно отправили в бот, можно обнулить состояние пользователя
            if sent:
                try:
                    await db_service.reset_user_after_premium_report(telegram_id)
                except Exception as e:
                    logger.error(f"⚠️ Не удалось сбросить состояние пользователя {telegram_id} после отправки отчета: {e}")
            
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            
            # Обновляем статус в БД
            await db_service.update_report_generation_status(
                telegram_id, 
                "premium", 
                ReportGenerationStatus.FAILED, 
                error=error_msg
            )
            
            # Отправляем уведомление об ошибке в Telegram
            from bot.services.telegram_service import telegram_service
            await telegram_service.send_error_notification(
                telegram_id=telegram_id,
                error_message=error_msg
            )
            
            logger.error(f"❌ Ошибка асинхронной генерации ПЛАТНОГО отчета для пользователя {telegram_id}: {error_msg}")
            
    except Exception as e:
        # Обновляем статус в БД
        await db_service.update_report_generation_status(
            telegram_id, 
            "premium", 
            ReportGenerationStatus.FAILED, 
            error=str(e)
        )
        
        # Отправляем уведомление об ошибке в Telegram
        from bot.services.telegram_service import telegram_service
        await telegram_service.send_error_notification(
            telegram_id=telegram_id,
            error_message=str(e)
        )
        
        logger.error(f"❌ Критическая ошибка асинхронной генерации ПЛАТНОГО отчета для пользователя {telegram_id}: {e}")

@app.get("/api/user/{telegram_id}/reports-status", summary="Проверить статус всех отчетов пользователя")
async def check_user_reports_status(telegram_id: int):
    """Проверить статус всех отчетов пользователя и определить какой доступен для скачивания"""
    try:
        logger.info(f"🔍 Проверка статуса отчетов для пользователя {telegram_id}")
        
        # Получаем пользователя ОДИН РАЗ
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {
                "status": "test_not_completed", 
                "message": "Тест не завершен",
                "available_report": None
            }
        
        # Проверяем статус бесплатного отчета (передаем уже полученного пользователя)
        free_report_status = await check_report_status_with_user(telegram_id, user)
        
        # Проверяем статус премиум отчета (передаем уже полученного пользователя)
        premium_report_status = await check_premium_report_status_with_user(telegram_id, user)
        
        logger.info(f"📊 Статус бесплатного отчета: {free_report_status.get('status')}")
        logger.info(f"📊 Статус премиум отчета: {premium_report_status.get('status')}")
        logger.info(f"💰 Пользователь оплатил: {user.is_paid}")
        
        # Определяем какой отчет доступен для скачивания
        available_report = None
        
        if user.is_paid and premium_report_status.get('status') == 'ready' and premium_report_status.get('report_path') and str(premium_report_status.get('report_path')).lower().endswith('.pdf'):
            # Если пользователь оплатил и премиум отчет готов
            available_report = {
                "type": "premium",
                "status": "ready",
                "message": "Премиум отчет готов к скачиванию",
                "download_url": f"/api/download/premium-report/{telegram_id}"
            }
        elif free_report_status.get('status') == 'ready':
            # Если бесплатный отчет готов (всегда доступен)
            available_report = {
                "type": "free",
                "status": "ready", 
                "message": "Бесплатный отчет готов к скачиванию",
                "download_url": f"/api/download/report/{telegram_id}"
            }
        elif free_report_status.get('status') == 'premium_paid':
            # Если пользователь оплатил премиум, но премиум отчет еще не готов
            if user.is_paid:
                available_report = {
                    "type": "premium",
                    "status": "not_started",
                    "message": "Премиум отчет еще не сгенерирован"
                }
            else:
                available_report = {
                    "type": "free",
                    "status": "premium_paid",
                    "message": "Для оплативших премиум пользователей используется премиум отчет"
                }
        elif premium_report_status.get('status') in ['processing', 'ready']:
            # Если премиум отчет в процессе генерации
            available_report = {
                "type": "premium",
                "status": "processing",
                "message": "Премиум отчет генерируется..."
            }
        elif premium_report_status.get('status') == 'payment_required':
            # Если требуется оплата для премиум отчета
            available_report = {
                "type": "premium",
                "status": "payment_required",
                "message": "Для доступа к премиум отчету требуется оплата"
            }
        elif user.is_paid and premium_report_status.get('status') == 'failed':
            # Если премиум отчет не удалось сгенерировать, но есть бесплатный
            if free_report_status.get('status') == 'ready':
                available_report = {
                    "type": "free",
                    "status": "ready",
                    "message": "Премиум отчет недоступен, но бесплатный отчет готов",
                    "download_url": f"/api/download/report/{telegram_id}",
                    "fallback": True
                }
            else:
                available_report = {
                    "type": "premium",
                    "status": "failed",
                    "message": "Ошибка генерации премиум отчета",
                    "error": premium_report_status.get('error', 'Неизвестная ошибка')
                }
        elif free_report_status.get('status') == 'processing':
            # Если бесплатный отчет в процессе генерации
            available_report = {
                "type": "free",
                "status": "processing",
                "message": "Бесплатный отчет генерируется..."
            }
        elif free_report_status.get('status') == 'failed':
            # Если бесплатный отчет не удалось сгенерировать
            available_report = {
                "type": "free",
                "status": "failed",
                "message": "Ошибка генерации бесплатного отчета",
                "error": free_report_status.get('error', 'Неизвестная ошибка')
            }
        else:
            # Если нет доступных отчетов
            available_report = {
                "type": "none",
                "status": "not_available",
                "message": "Нет доступных отчетов"
            }
        
        return {
            "status": "success",
            "user_id": telegram_id,
            "test_completed": user.test_completed,
            "is_paid": user.is_paid,
            "free_report_status": free_report_status,
            "premium_report_status": premium_report_status,
            "available_report": available_report
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке статуса отчетов для пользователя {telegram_id}: {e}")
        return {
            "status": "error",
            "message": f"Ошибка при проверке статуса отчетов: {str(e)}",
            "available_report": None
        }

# Вспомогательные функции для работы с уже полученным пользователем
async def check_report_status_with_user(telegram_id: int, user: User):
    """Проверить готовность отчета пользователя (с уже полученным пользователем)"""
    try:
        if not user.test_completed:
            return {"status": "test_not_completed", "message": "Тест не завершен"}
        
        # Проверяем, не оплатил ли пользователь премиум отчет
        if user.is_paid:
            logger.info(f"💰 Пользователь {telegram_id} оплатил премиум отчет. Не возвращаем статус бесплатного отчета.")
            return {"status": "premium_paid", "message": "Для оплативших премиум пользователей используется премиум отчет."}
        
        # Ищем последний отчет пользователя
        reports_dir = Path("reports")
        pattern = f"prizma_report_{telegram_id}_*.pdf"
        
        import glob
        report_files = glob.glob(str(reports_dir / pattern))
        
        if report_files:
            # Сортируем по timestamp в имени файла (более надежно чем st_mtime)
            # Имя файла: prizma_report_{telegram_id}_{timestamp}.pdf
            def extract_timestamp(filepath):
                filename = Path(filepath).name
                # Извлекаем timestamp из имени файла: prizma_report_123456789_20250627_082506.pdf
                parts = filename.split('_')
                if len(parts) >= 5:
                    try:
                        # Берем дату и время: parts[3] = '20250627', parts[4] = '082506.pdf'
                        date_part = parts[3]
                        time_part = parts[4].replace('.pdf', '').replace('.txt', '')
                        timestamp_str = f"{date_part}_{time_part}"
                        return timestamp_str
                    except:
                        return "00000000_000000"
                return "00000000_000000"
                
            # Находим последний файл по timestamp
            latest_report = max(report_files, key=extract_timestamp)
            # Дополнительная проверка существования файла
            if os.path.exists(latest_report):
                return {"status": "ready", "message": "Отчет готов к скачиванию", "report_path": latest_report}
            else:
                return {"status": "not_ready", "message": "Отчет еще не готов"}
        else:
            return {"status": "not_ready", "message": "Отчет еще не готов"}
            
    except Exception as e:
        logger.error(f"Error checking report status: {e}")
        return {"status": "error", "message": "Ошибка при проверке статуса отчета"}

async def check_premium_report_status_with_user(telegram_id: int, user: User):
    """Проверить статус готовности платного отчета пользователя (с уже полученным пользователем)"""
    try:
        if not user.test_completed:
            return {"status": "test_not_completed", "message": "Тест не завершен"}
        
        # Проверяем, оплатил ли пользователь премиум отчет
        if not user.is_paid:
            return {"status": "payment_required", "message": "Для доступа к премиум отчету требуется оплата."}
        
        # Проверяем и сбрасываем зависшие отчеты
        await db_service.reset_stuck_reports(telegram_id)
        
        # Получаем статус генерации из БД
        status_info = await db_service.get_report_generation_status(telegram_id, "premium")
        logger.info(f"📊 Получен статус премиум отчета для пользователя {telegram_id}: {status_info}")
        
        # Если в БД COMPLETED – проверяем реальное наличие файла и что это именно PDF
        if status_info.get("status") == "COMPLETED" and status_info.get("report_path"):
            report_path = status_info["report_path"]
            # Файл должен существовать и быть PDF
            if os.path.exists(report_path) and report_path.lower().endswith('.pdf'):
                return {
                    "status": "ready", 
                    "message": "Премиум отчет готов к скачиванию", 
                    "report_path": report_path
                }
            else:
                # Если файла нет или это не PDF (например .txt fallback) – считаем, что отчет еще не готов
                return {
                    "status": "processing",
                    "message": "Премиум отчет еще генерируется"
                }
        elif status_info.get("status") == "PROCESSING":
            return {"status": "processing", "message": "Отчет генерируется..."}
        elif status_info.get("status") == "FAILED":
            return {
                "status": "failed", 
                "message": "Ошибка генерации отчета", 
                "error": status_info.get("error", "Неизвестная ошибка")
            }
        else:
            logger.info(f"📊 Статус премиум отчета для пользователя {telegram_id}: not_started (статус из БД: {status_info.get('status')})")
            return {"status": "not_started", "message": "Генерация не запущена"}
            
    except Exception as e:
        logger.error(f"Error checking premium report status: {e}")
        return {"status": "error", "message": "Ошибка при проверке статуса платного отчета"}

# Подключение статических файлов в конце (после всех API маршрутов)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")