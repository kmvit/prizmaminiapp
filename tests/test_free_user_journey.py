#!/usr/bin/env python3
"""
Тест: Полный путь бесплатного пользователя
- Регистрация пользователя
- Прохождение теста (10 вопросов)
- Генерация бесплатного отчета
- Проверка статусов отчетов
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Добавляем корневую директорию проекта в путь
sys.path.append(str(Path(__file__).parent.parent))

from bot.services.database_service import db_service
from bot.services.perplexity import AIAnalysisService
from bot.services.pdf_service import ReportGenerator
from bot.database.models import User, Question, Answer, ReportGenerationStatus
from bot.web_app import check_user_reports_status, check_report_status_with_user

class TestFreeUserJourney:
    """Тест полного пути бесплатного пользователя"""
    
    def __init__(self):
        self.telegram_id = 123456789
        self.user = None
        self.questions = []
        self.answers = []
    
    async def setup_test_data(self):
        """Подготовка тестовых данных"""
        print("📋 Подготовка тестовых данных...")
        
        # Сначала удаляем существующего пользователя, если он есть
        await db_service.delete_user(self.telegram_id)
        
        # Создаем пользователя
        self.user = await db_service.get_or_create_user(
            telegram_id=self.telegram_id,
            first_name="Тест",
            last_name="Пользователь",
            username="test_user"
        )
        print(f"✅ Пользователь создан: {self.user.telegram_id}")
        
        # Очищаем статусы отчетов
        await db_service.clear_report_statuses(self.telegram_id)
        
        # Загружаем вопросы и ответы
        path = Path("data/questions_with_answers.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Берем только первые 10 вопросов (бесплатные)
        for item in data["questions"]:
            if item["order_number"] > 10:
                break
            self.questions.append(item)
            self.answers.append({
                "question_id": item["order_number"],
                "text_answer": item["answer"]
            })
        
        print(f"✅ Загружено вопросов: {len(self.questions)}, ответов: {len(self.answers)}")
    
    async def test_user_registration(self):
        """Тест регистрации пользователя"""
        print("\n🔐 Тест регистрации пользователя...")
        
        # Проверяем, что пользователь создан
        assert self.user is not None, "Пользователь не создан"
        assert self.user.telegram_id == self.telegram_id, "Неверный telegram_id"
        assert self.user.first_name == "Тест", "Неверное имя"
        assert not self.user.is_paid, "Пользователь должен быть бесплатным"
        assert not self.user.test_completed, "Тест не должен быть завершен"
        
        print("✅ Регистрация пользователя прошла успешно")
    
    async def test_start_test(self):
        """Тест начала теста"""
        print("\n🚀 Тест начала теста...")
        
        # Начинаем тест
        user = await db_service.start_test(self.telegram_id)
        
        assert user.test_started_at is not None, "Время начала теста не установлено"
        assert user.current_question_id is not None, "Текущий вопрос не установлен"
        assert not user.test_completed, "Тест не должен быть завершен"
        
        print("✅ Тест успешно начат")
    
    async def test_answer_questions(self):
        """Тест ответов на вопросы"""
        print("\n📝 Тест ответов на вопросы...")
        
        for i, (question, answer) in enumerate(zip(self.questions, self.answers)):
            print(f"   Вопрос {i+1}/{len(self.questions)}: {question['text'][:50]}...")
            
            # Сохраняем ответ
            saved_answer = await db_service.save_answer(
                telegram_id=self.telegram_id,
                question_id=answer["question_id"],
                text_answer=answer["text_answer"]
            )
            
            assert saved_answer is not None, f"Ответ на вопрос {i+1} не сохранен"
            assert saved_answer.text_answer == answer["text_answer"], "Текст ответа не совпадает"
        
        print("✅ Все ответы сохранены успешно")
    
    async def test_complete_test(self):
        """Тест завершения теста"""
        print("\n🏁 Тест завершения теста...")
        
        # Завершаем тест
        user = await db_service.complete_test(self.telegram_id)
        
        assert user.test_completed, "Тест должен быть завершен"
        assert user.test_completed_at is not None, "Время завершения теста не установлено"
        assert user.current_question_id is None, "Текущий вопрос должен быть сброшен"
        
        print("✅ Тест успешно завершен")
    
    async def test_check_reports_status_before_generation(self):
        """Тест проверки статуса отчетов до генерации"""
        print("\n📊 Тест проверки статуса отчетов (до генерации)...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        
        assert status_response["status"] == "success", "Статус должен быть success"
        assert status_response["test_completed"] == True, "Тест должен быть завершен"
        assert status_response["is_paid"] == False, "Пользователь должен быть бесплатным"
        
        # Проверяем статус бесплатного отчета
        free_status = status_response["free_report_status"]
        assert free_status["status"] == "not_ready", "Бесплатный отчет не должен быть готов"
        
        print("✅ Статус отчетов корректный (отчет еще не готов)")
    
    async def test_generate_free_report(self):
        """Тест генерации бесплатного отчета"""
        print("\n🤖 Тест генерации бесплатного отчета...")
        
        # Получаем ответы пользователя
        user_answers = await db_service.get_user_answers(self.telegram_id)
        assert len(user_answers) > 0, "Ответы пользователя не найдены"
        
        # Получаем вопросы
        questions = await db_service.get_questions()
        assert len(questions) > 0, "Вопросы не найдены"
        
        # Генерируем отчет через AI сервис
        ai_service = AIAnalysisService()
        result = await ai_service.generate_psychological_report(self.user, questions, user_answers)
        
        assert result.get("success"), f"Ошибка генерации отчета: {result.get('error')}"
        assert "report_file" in result, "Путь к отчету не найден"
        
        report_path = result["report_file"]
        assert Path(report_path).exists(), f"Файл отчета не найден: {report_path}"
        
        print(f"✅ Бесплатный отчет успешно сгенерирован: {report_path}")
        
        # Проверяем размер файла
        size_kb = Path(report_path).stat().st_size / 1024
        print(f"📏 Размер отчета: {size_kb:.1f} KB")
        assert size_kb > 0, "Размер отчета должен быть больше 0"
    
    async def test_check_reports_status_after_generation(self):
        """Тест проверки статуса отчетов после генерации"""
        print("\n📊 Тест проверки статуса отчетов (после генерации)...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        
        assert status_response["status"] == "success", "Статус должен быть success"
        
        # Проверяем статус бесплатного отчета
        free_status = status_response["free_report_status"]
        assert free_status["status"] == "ready", "Бесплатный отчет должен быть готов"
        assert "report_path" in free_status, "Путь к отчету должен быть указан"
        
        # Проверяем доступный отчет
        available_report = status_response["available_report"]
        assert available_report["type"] == "free", "Доступный отчет должен быть бесплатным"
        assert available_report["status"] == "ready", "Доступный отчет должен быть готов"
        
        print("✅ Статус отчетов корректный (отчет готов)")
    
    async def test_download_report(self):
        """Тест скачивания отчета"""
        print("\n📥 Тест скачивания отчета...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        free_status = status_response["free_report_status"]
        
        if free_status["status"] == "ready" and "report_path" in free_status:
            report_path = free_status["report_path"]
            assert Path(report_path).exists(), f"Файл отчета не найден: {report_path}"
            
            # Проверяем, что файл можно прочитать
            with open(report_path, 'rb') as f:
                content = f.read()
                assert len(content) > 0, "Файл отчета пустой"
            
            print(f"✅ Отчет готов к скачиванию: {report_path}")
        else:
            print("⚠️ Отчет еще не готов к скачиванию")
    
    async def run_full_journey(self):
        """Запуск полного теста пути пользователя"""
        print("=" * 60)
        print("🚀 ЗАПУСК ТЕСТА: Полный путь бесплатного пользователя")
        print("=" * 60)
        
        try:
            # Подготовка данных
            await self.setup_test_data()
            
            # Тесты
            await self.test_user_registration()
            await self.test_start_test()
            await self.test_answer_questions()
            await self.test_complete_test()
            await self.test_check_reports_status_before_generation()
            await self.test_generate_free_report()
            await self.test_check_reports_status_after_generation()
            await self.test_download_report()
            
            print("\n" + "=" * 60)
            print("✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ОШИБКА В ТЕСТЕ: {e}")
            raise e

async def main():
    """Главная функция для запуска теста"""
    test = TestFreeUserJourney()
    await test.run_full_journey()

if __name__ == "__main__":
    asyncio.run(main()) 