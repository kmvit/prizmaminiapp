#!/usr/bin/env python3
"""
Тест: Полный путь платного пользователя
- Регистрация пользователя
- Прохождение полного теста (50 вопросов)
- Оплата премиум отчета
- Генерация премиум отчета
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
from bot.database.models import User, Question, Answer, ReportGenerationStatus, PaymentStatus
from bot.web_app import check_user_reports_status, check_premium_report_status_with_user

class TestPremiumUserJourney:
    """Тест полного пути платного пользователя"""
    
    def __init__(self):
        self.telegram_id = 987654321
        self.user = None
        self.questions = []
        self.answers = []
        self.payment = None
    
    async def setup_test_data(self):
        """Подготовка тестовых данных"""
        print("📋 Подготовка тестовых данных...")
        
        # Сначала удаляем существующего пользователя, если он есть
        await db_service.delete_user(self.telegram_id)
        
        # Создаем пользователя
        self.user = await db_service.get_or_create_user(
            telegram_id=self.telegram_id,
            first_name="Премиум",
            last_name="Пользователь",
            username="premium_user"
        )
        print(f"✅ Пользователь создан: {self.user.telegram_id}")
        
        # Очищаем статусы отчетов
        await db_service.clear_report_statuses(self.telegram_id)
        
        # Загружаем вопросы и ответы
        path = Path("data/questions_with_answers.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Берем все 50 вопросов (премиум)
        for item in data["questions"]:
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
        assert self.user.first_name == "Премиум", "Неверное имя"
        assert not self.user.is_paid, "Пользователь должен быть бесплатным изначально"
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
    
    async def test_answer_all_questions(self):
        """Тест ответов на все вопросы (50)"""
        print("\n📝 Тест ответов на все вопросы...")
        
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
    
    async def test_create_payment(self):
        """Тест создания платежа"""
        print("\n💳 Тест создания платежа...")
        
        # Создаем платеж
        self.payment = await db_service.create_payment(
            user_id=self.user.id,
            amount=10000,  # 100 рублей в копейках
            currency="RUB",
            description="Оплата премиум отчета",
            invoice_id="test_invoice_123",
            status=PaymentStatus.PENDING
        )
        
        assert self.payment is not None, "Платеж не создан"
        assert self.payment.user_id == self.user.id, "Неверный user_id в платеже"
        assert self.payment.amount == 10000, "Неверная сумма платежа"
        assert self.payment.status == PaymentStatus.PENDING, "Неверный статус платежа"
        
        print("✅ Платеж успешно создан")
    
    async def test_complete_payment(self):
        """Тест завершения платежа"""
        print("\n✅ Тест завершения платежа...")
        
        # Завершаем платеж
        updated_payment = await db_service.update_payment_status(
            payment_id=self.payment.id,
            status=PaymentStatus.COMPLETED,
            robokassa_payment_id="test_robokassa_123"
        )
        
        assert updated_payment.status == PaymentStatus.COMPLETED, "Статус платежа не обновлен"
        assert updated_payment.paid_at is not None, "Время оплаты не установлено"
        
        # Обновляем статус пользователя
        user = await db_service.upgrade_to_paid(self.telegram_id)
        assert user.is_paid == True, "Статус пользователя не обновлен"
        
        print("✅ Платеж успешно завершен, пользователь стал платным")
    
    async def test_check_reports_status_before_premium_generation(self):
        """Тест проверки статуса отчетов до генерации премиум отчета"""
        print("\n📊 Тест проверки статуса отчетов (до генерации премиум)...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        
        assert status_response["status"] == "success", "Статус должен быть success"
        assert status_response["test_completed"] == True, "Тест должен быть завершен"
        assert status_response["is_paid"] == True, "Пользователь должен быть платным"
        
        # Проверяем статус бесплатного отчета (должен быть premium_paid)
        free_status = status_response["free_report_status"]
        assert free_status["status"] == "premium_paid", "Бесплатный отчет должен быть premium_paid"
        
        # Проверяем статус премиум отчета
        premium_status = status_response["premium_report_status"]
        assert premium_status["status"] == "not_started", "Премиум отчет не должен быть запущен"
        
        print("✅ Статус отчетов корректный (премиум отчет еще не готов)")
    
    async def test_generate_premium_report(self):
        """Тест генерации премиум отчета"""
        print("\n🤖 Тест генерации премиум отчета...")
        
        # Получаем ответы пользователя
        user_answers = await db_service.get_user_answers(self.telegram_id)
        assert len(user_answers) > 0, "Ответы пользователя не найдены"
        assert len(user_answers) == 50, f"Должно быть 50 ответов, найдено {len(user_answers)}"
        
        # Получаем вопросы
        questions = await db_service.get_questions()
        assert len(questions) > 0, "Вопросы не найдены"
        
        # Генерируем премиум отчет через AI сервис
        ai_service = AIAnalysisService()
        result = await ai_service.generate_premium_report(self.user, questions, user_answers)
        
        assert result.get("success"), f"Ошибка генерации премиум отчета: {result.get('error')}"
        assert "report_file" in result, "Путь к премиум отчету не найден"
        
        report_path = result["report_file"]
        assert Path(report_path).exists(), f"Файл премиум отчета не найден: {report_path}"
        
        print(f"✅ Премиум отчет успешно сгенерирован: {report_path}")
        
        # Проверяем размер файла
        size_kb = Path(report_path).stat().st_size / 1024
        print(f"📏 Размер премиум отчета: {size_kb:.1f} KB")
        assert size_kb > 0, "Размер премиум отчета должен быть больше 0"
    
    async def test_check_reports_status_after_premium_generation(self):
        """Тест проверки статуса отчетов после генерации премиум отчета"""
        print("\n📊 Тест проверки статуса отчетов (после генерации премиум)...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        
        assert status_response["status"] == "success", "Статус должен быть success"
        
        # Проверяем статус премиум отчета
        premium_status = status_response["premium_report_status"]
        assert premium_status["status"] == "ready", "Премиум отчет должен быть готов"
        assert "report_path" in premium_status, "Путь к премиум отчету должен быть указан"
        
        # Проверяем доступный отчет
        available_report = status_response["available_report"]
        assert available_report["type"] == "premium", "Доступный отчет должен быть премиум"
        assert available_report["status"] == "ready", "Доступный отчет должен быть готов"
        
        print("✅ Статус отчетов корректный (премиум отчет готов)")
    
    async def test_download_premium_report(self):
        """Тест скачивания премиум отчета"""
        print("\n📥 Тест скачивания премиум отчета...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        premium_status = status_response["premium_report_status"]
        
        if premium_status["status"] == "ready" and "report_path" in premium_status:
            report_path = premium_status["report_path"]
            assert Path(report_path).exists(), f"Файл премиум отчета не найден: {report_path}"
            
            # Проверяем, что файл можно прочитать
            with open(report_path, 'rb') as f:
                content = f.read()
                assert len(content) > 0, "Файл премиум отчета пустой"
            
            print(f"✅ Премиум отчет готов к скачиванию: {report_path}")
        else:
            print("⚠️ Премиум отчет еще не готов к скачиванию")
    
    async def test_premium_report_vs_free_report(self):
        """Тест сравнения премиум и бесплатного отчетов"""
        print("\n🔍 Тест сравнения отчетов...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        
        # Для платного пользователя должен быть доступен премиум отчет
        available_report = status_response["available_report"]
        assert available_report["type"] == "premium", "Для платного пользователя должен быть доступен премиум отчет"
        
        # Бесплатный отчет должен быть недоступен
        free_status = status_response["free_report_status"]
        assert free_status["status"] == "premium_paid", "Бесплатный отчет должен быть недоступен для платного пользователя"
        
        print("✅ Логика отчетов работает корректно (премиум приоритетнее бесплатного)")
    
    async def run_full_journey(self):
        """Запуск полного теста пути платного пользователя"""
        print("=" * 60)
        print("🚀 ЗАПУСК ТЕСТА: Полный путь платного пользователя")
        print("=" * 60)
        
        try:
            # Подготовка данных
            await self.setup_test_data()
            
            # Тесты
            await self.test_user_registration()
            await self.test_start_test()
            await self.test_answer_all_questions()
            await self.test_complete_test()
            await self.test_create_payment()
            await self.test_complete_payment()
            await self.test_check_reports_status_before_premium_generation()
            await self.test_generate_premium_report()
            await self.test_check_reports_status_after_premium_generation()
            await self.test_download_premium_report()
            await self.test_premium_report_vs_free_report()
            
            print("\n" + "=" * 60)
            print("✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ОШИБКА В ТЕСТЕ: {e}")
            raise e

async def main():
    """Главная функция для запуска теста"""
    test = TestPremiumUserJourney()
    await test.run_full_journey()

if __name__ == "__main__":
    asyncio.run(main()) 