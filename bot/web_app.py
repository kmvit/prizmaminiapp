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

@app.get("/api/user/{telegram_id}/report-status", summary="Проверить статус генерации отчета")
async def check_report_status(telegram_id: int):
    """Проверить готовность отчета пользователя"""
    try:
        # Проверяем, что пользователь завершил тест
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {"status": "test_not_completed", "message": "Тест не завершен"}
        
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
        
        logger.info(f"🚀 Запускаем синхронную генерацию отчета для пользователя {telegram_id}")
        
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
            return report_path
        else:
            logger.error(f"❌ Ошибка фоновой генерации отчета для пользователя {telegram_id}: {result.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка фоновой генерации отчета для пользователя {telegram_id}: {e}")
        return None

# ПЛАТНАЯ ВЕРСИЯ - новые эндпоинты

@app.get("/api/user/{telegram_id}/premium-report-status", summary="Проверить статус генерации платного отчета")
async def check_premium_report_status(telegram_id: int):
    """Проверить статус готовности платного отчета пользователя"""
    try:
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {"status": "test_not_completed", "message": "Тест не завершен"}
        
        # Ищем последний платный отчет пользователя
        reports_dir = Path("reports")
        pattern = f"prizma_premium_report_{telegram_id}_*.pdf"
        
        import glob
        report_files = glob.glob(str(reports_dir / pattern))
        
        if report_files:
            # Сортируем по timestamp в имени файла
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
                        return "00000000_000000"
                return "00000000_000000"
                
            latest_report = max(report_files, key=extract_timestamp)
            return {"status": "ready", "message": "Платный отчет готов к скачиванию", "report_path": latest_report}
        else:
            return {"status": "not_ready", "message": "Платный отчет еще не готов"}
            
    except Exception as e:
        logger.error(f"Error checking premium report status: {e}")
        return {"status": "error", "message": "Ошибка при проверке статуса платного отчета"}

@app.post("/api/user/{telegram_id}/generate-premium-report", summary="Запустить генерацию платного отчета")
async def start_premium_report_generation(telegram_id: int):
    """Запустить генерацию платного отчета пользователя (50 вопросов)"""
    try:
        # Проверяем, что пользователь завершил тест
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            return {"status": "error", "message": "Тест не завершен"}
        
        logger.info(f"🚀 Запускаем синхронную генерацию ПЛАТНОГО отчета для пользователя {telegram_id}")
        
        # Запускаем синхронную генерацию платного отчета
        report_path = await generate_premium_report_background(telegram_id)
        
        if report_path:
            return {"status": "success", "message": "Платный отчет успешно сгенерирован", "report_path": report_path}
        else:
            return {"status": "error", "message": "Ошибка при генерации платного отчета"}
            
    except Exception as e:
        logger.error(f"Error starting premium report generation: {e}")
        return {"status": "error", "message": f"Ошибка при генерации платного отчета: {str(e)}"}

@app.get("/api/download/premium-report/{telegram_id}", summary="Скачать платный персональный отчет")
async def download_premium_personal_report(telegram_id: int, download: Optional[str] = None, method: Optional[str] = None, t: Optional[str] = None):
    """Скачать готовый платный персональный отчет пользователя (50 вопросов)"""
    from fastapi.responses import FileResponse
    import os
    import glob
    
    try:
        logger.info(f"📁 Запрос скачивания ПЛАТНОГО отчета для пользователя {telegram_id}")
        logger.info(f"📊 Параметры: download={download}, method={method}, t={t}")
        
        # Проверяем, что пользователь завершил тест
        user = await db_service.get_or_create_user(telegram_id=telegram_id)
        
        if not user.test_completed:
            logger.warning(f"⚠️ Пользователь {telegram_id} не завершил тест")
            raise HTTPException(status_code=400, detail="Тест не завершен. Завершите тест для получения платного отчета.")
        
        # Ищем готовый платный отчет пользователя
        reports_dir = Path("reports")
        pattern = f"prizma_premium_report_{telegram_id}_*.pdf"
        report_files = glob.glob(str(reports_dir / pattern))
        
        if not report_files:
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

# Функция фоновой генерации платного отчета
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

# Подключение статических файлов в конце (после всех API маршрутов)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")