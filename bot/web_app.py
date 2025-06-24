from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional
from datetime import datetime

from bot.services.database_service import db_service
from bot.config import BASE_DIR, PERPLEXITY_ENABLED
from bot.models.api_models import (
    AnswerRequest, UserProfileUpdate, CurrentQuestionResponse, 
    NextQuestionResponse, UserProgressResponse, UserProfileResponse,
    QuestionResponse, ProgressResponse, UserStatusResponse, ErrorResponse
)
from loguru import logger

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
            user = await db_service.start_test(telegram_id)
        
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
                current=answered_count + 1,
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
        # Получаем пользователя
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.current_question_id:
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
        
        # Анализируем ответ через ИИ (если включено)
        if PERPLEXITY_ENABLED:
            try:
                from bot.services.perplexity import perplexity_service
                analysis_result = await perplexity_service.analyze_text(answer_data.text_answer)
                ai_analysis = analysis_result['choices'][0]['message']['content']
                await db_service.update_answer_analysis(answer.id, ai_analysis)
                logger.info(f"✅ ИИ-анализ выполнен для ответа {answer.id}")
            except Exception as api_error:
                logger.error(f"Perplexity API error: {api_error}")
        else:
            # Perplexity отключен - сохраняем ответ без анализа
            logger.info(f"ℹ️ Perplexity отключен - ответ {answer.id} сохранен без ИИ-анализа")
        
        # Получаем следующий вопрос
        next_question = await db_service.get_next_question(
            current_question.id,
            user.is_paid
        )
        
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
                    current=answered_count + 1,
                    total=total_questions,
                    answered=answered_count
                )
            )
        else:
            # Тест завершен
            await db_service.complete_test(telegram_id)
            
            return NextQuestionResponse(
                status="test_completed",
                message="Поздравляем! Вы завершили тест."
            )
            
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
        
        return UserProfileResponse(
            status="success",
            user={
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "name": user.name,
                "age": user.age,
                "gender": user.gender
            }
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
        
        return UserProfileResponse(
            status="success",
            user={
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "name": user.name,
                "age": user.age,
                "gender": user.gender
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

# Обработчик ошибок
from fastapi.responses import JSONResponse

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

@app.get("/api/download/report/{telegram_id}", summary="Скачать персональный отчет")
async def download_personal_report(telegram_id: int, download: Optional[str] = None, method: Optional[str] = None, t: Optional[str] = None):
    """Генерировать и скачать персональный отчет пользователя"""
    from fastapi.responses import FileResponse
    from fastapi import Request
    from bot.services.report_generator import report_generator
    import os
    
    try:
        logger.info(f"📁 Запрос скачивания отчета для пользователя {telegram_id}")
        logger.info(f"📊 Параметры: download={download}, method={method}, t={t}")
        
        # Проверяем, что пользователь завершил тест
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            logger.warning(f"⚠️ Пользователь {telegram_id} не завершил тест")
            raise HTTPException(status_code=400, detail="Тест не завершен. Завершите тест для получения отчета.")
        
        # Получаем ответы пользователя
        answers = await db_service.get_user_answers(telegram_id)
        
        if not answers:
            logger.warning(f"⚠️ У пользователя {telegram_id} нет ответов")
            raise HTTPException(status_code=400, detail="У пользователя нет ответов для генерации отчета.")
        
        logger.info(f"✅ Пользователь {telegram_id} прошел проверки, генерируем отчет...")
        
        # Генерируем персональный отчет
        report_path = await report_generator.generate_report(user, answers)
        
        if not os.path.exists(report_path):
            logger.error(f"❌ Файл отчета не найден: {report_path}")
            raise HTTPException(status_code=500, detail="Ошибка при генерации отчета")
        
        logger.info(f"📄 Отчет готов: {report_path}, размер: {os.path.getsize(report_path)} байт")
        
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
            path=report_path,
            media_type='application/pdf',
            filename=f"prizma-report-{telegram_id}.pdf",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating/downloading report: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при генерации отчета")

# Подключение статических файлов в конце (после всех API маршрутов)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")