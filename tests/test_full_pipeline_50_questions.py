#!/usr/bin/env python3
"""
Комплексный тест: Полный пайплайн с 50 вопросами (только премиум отчет)
- Регистрация пользователя
- Прохождение всех 50 вопросов
- Оплата премиум отчета
- Генерация премиум отчета (50 вопросов)
- Проверка ответов от ИИ в премиум отчете
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
from bot.web_app import check_user_reports_status, check_report_status_with_user
from bot.config import PERPLEXITY_ENABLED


class TestFullPipeline50Questions:
    """Комплексный тест полного пайплайна с 50 вопросами (только премиум отчет)"""
    
    def __init__(self):
        self.telegram_id = 999888777
        self.user = None
        self.questions = []
        self.answers = []
        self.premium_report_path = None
    
    async def setup_test_data(self):
        """Подготовка тестовых данных"""
        print("📋 Подготовка тестовых данных...")
        
        # Проверяем, включен ли Perplexity API
        if not PERPLEXITY_ENABLED:
            print("⚠️ ВНИМАНИЕ: Perplexity API отключен. Тест будет работать, но ИИ-анализ не будет получен.")
            print("   Для полного теста установите PERPLEXITY_ENABLED=true и PERPLEXITY_API_KEY в .env")
        
        # Сначала удаляем существующего пользователя, если он есть
        await db_service.delete_user(self.telegram_id)
        
        # Создаем пользователя
        self.user = await db_service.get_or_create_user(
            telegram_id=self.telegram_id,
            first_name="Полный",
            last_name="Тест",
            username="full_test_user"
        )
        print(f"✅ Пользователь создан: {self.user.telegram_id}")
        
        # Очищаем статусы отчетов
        await db_service.clear_report_statuses(self.telegram_id)
        
        # Загружаем вопросы и ответы
        path = Path("data/questions_with_answers.json")
        if not path.exists():
            raise FileNotFoundError(f"Файл {path} не найден. Необходим для теста.")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Берем все 50 вопросов
        for item in data["questions"]:
            if item["order_number"] > 50:
                break
            self.questions.append(item)
            self.answers.append({
                "question_id": item["order_number"],
                "text_answer": item["answer"]
            })
        
        print(f"✅ Загружено вопросов: {len(self.questions)}, ответов: {len(self.answers)}")
        assert len(self.questions) == 50, f"Ожидалось 50 вопросов, получено {len(self.questions)}"
    
    async def test_user_registration(self):
        """Тест регистрации пользователя"""
        print("\n🔐 Тест регистрации пользователя...")
        
        assert self.user is not None, "Пользователь не создан"
        assert self.user.telegram_id == self.telegram_id, "Неверный telegram_id"
        assert not self.user.is_paid, "Пользователь должен быть бесплатным изначально"
        assert not self.user.test_completed, "Тест не должен быть завершен"
        
        print("✅ Регистрация пользователя прошла успешно")
    
    async def test_start_test(self):
        """Тест начала теста"""
        print("\n🚀 Тест начала теста...")
        
        user = await db_service.start_test(self.telegram_id)
        
        assert user.test_started_at is not None, "Время начала теста не установлено"
        assert user.current_question_id is not None, "Текущий вопрос не установлен"
        assert not user.test_completed, "Тест не должен быть завершен"
        
        print("✅ Тест успешно начат")
    
    async def test_answer_all_50_questions(self):
        """Тест ответов на все 50 вопросов"""
        print("\n📝 Тест ответов на все 50 вопросов...")
        print(f"   Всего вопросов: {len(self.questions)}")
        print("\n" + "="*80)
        print("📋 ВОПРОСЫ И ОТВЕТЫ:")
        print("="*80)
        
        for i, (question, answer) in enumerate(zip(self.questions, self.answers)):
            print(f"\n--- Вопрос {i+1}/50 ---")
            print(f"❓ {question['text']}")
            print(f"💬 Ответ: {answer['text_answer']}")
            
            # Сохраняем ответ
            saved_answer = await db_service.save_answer(
                telegram_id=self.telegram_id,
                question_id=answer["question_id"],
                text_answer=answer["text_answer"]
            )
            
            assert saved_answer is not None, f"Ответ на вопрос {i+1} не сохранен"
            assert saved_answer.text_answer == answer["text_answer"], "Текст ответа не совпадает"
        
        print("\n" + "="*80)
        print("✅ Все 50 ответов сохранены успешно")
        print("="*80)
        
        # Проверяем, что все ответы сохранены
        user_answers = await db_service.get_user_answers(self.telegram_id)
        assert len(user_answers) == 50, f"Ожидалось 50 ответов, найдено {len(user_answers)}"
    
    async def test_complete_test(self):
        """Тест завершения теста"""
        print("\n🏁 Тест завершения теста...")
        
        user = await db_service.complete_test(self.telegram_id)
        
        assert user.test_completed, "Тест должен быть завершен"
        assert user.test_completed_at is not None, "Время завершения теста не установлено"
        assert user.current_question_id is None, "Текущий вопрос должен быть сброшен"
        
        print("✅ Тест успешно завершен (50 вопросов)")
    
    async def test_create_and_complete_payment(self):
        """Тест создания и завершения платежа"""
        print("\n💳 Тест создания и завершения платежа...")
        
        # Создаем платеж
        payment = await db_service.create_payment(
            user_id=self.user.id,
            amount=698000,  # 6980 рублей в копейках
            currency="RUB",
            description="Оплата премиум отчета (тест)",
            invoice_id="test_invoice_full_pipeline",
            status=PaymentStatus.PENDING
        )
        
        assert payment is not None, "Платеж не создан"
        assert payment.user_id == self.user.id, "Неверный user_id в платеже"
        assert payment.amount == 698000, "Неверная сумма платежа"
        assert payment.status == PaymentStatus.PENDING, "Неверный статус платежа"
        
        print("✅ Платеж успешно создан")
        
        # Завершаем платеж
        updated_payment = await db_service.update_payment_status(
            payment_id=payment.id,
            status=PaymentStatus.COMPLETED,
            robokassa_payment_id="test_robokassa_full_pipeline"
        )
        
        assert updated_payment.status == PaymentStatus.COMPLETED, "Статус платежа не обновлен"
        assert updated_payment.paid_at is not None, "Время оплаты не установлено"
        
        # Обновляем статус пользователя
        user = await db_service.upgrade_to_paid(self.telegram_id)
        assert user.is_paid == True, "Статус пользователя не обновлен"
        
        print("✅ Платеж успешно завершен, пользователь стал платным")
    
    async def test_generate_premium_report(self):
        """Тест генерации премиум отчета (50 вопросов)"""
        print("\n🤖 Тест генерации премиум отчета...")
        
        # Получаем все ответы пользователя (50 вопросов)
        user_answers = await db_service.get_user_answers(self.telegram_id)
        assert len(user_answers) == 50, f"Должно быть 50 ответов, найдено {len(user_answers)}"
        
        # Получаем все вопросы
        questions = await db_service.get_questions()
        assert len(questions) >= 50, f"Должно быть минимум 50 вопросов, найдено {len(questions)}"
        
        # Выводим все вопросы и ответы для премиум отчета
        print("\n" + "="*80)
        print("📋 ВСЕ ВОПРОСЫ И ОТВЕТЫ ДЛЯ ПРЕМИУМ ОТЧЕТА (50 вопросов):")
        print("="*80)
        for i, answer in enumerate(user_answers, 1):
            question = next((q for q in questions if q.id == answer.question_id), None)
            if question:
                print(f"\n--- Вопрос {i}/50 ---")
                print(f"❓ {question.text}")
                print(f"💬 Ответ: {answer.text_answer}")
        print("="*80)
        
        # Генерируем премиум отчет через AI сервис
        print("\n🤖 Начинаем генерацию премиум отчета с ИИ-анализом...")
        ai_service = AIAnalysisService()
        result = await ai_service.generate_premium_report(self.user, questions, user_answers)
        
        assert result.get("success"), f"Ошибка генерации премиум отчета: {result.get('error')}"
        assert "report_file" in result, "Путь к премиум отчету не найден"
        
        self.premium_report_path = result["report_file"]
        assert Path(self.premium_report_path).exists(), f"Файл премиум отчета не найден: {self.premium_report_path}"
        
        # Проверяем наличие ИИ-анализа
        if PERPLEXITY_ENABLED:
            assert "premium_analysis" in result, "ИИ-анализ (premium_analysis) не найден в результате"
            assert "premium_strengths" in result, "ИИ-анализ (premium_strengths) не найден в результате"
            assert "premium_growth_zones" in result, "ИИ-анализ (premium_growth_zones) не найден в результате"
            
            premium_analysis_length = len(result["premium_analysis"])
            premium_strengths_length = len(result["premium_strengths"])
            premium_growth_zones_length = len(result["premium_growth_zones"])
            
            print("\n" + "="*80)
            print("📊 РЕЗУЛЬТАТЫ ИИ-АНАЛИЗА (ПРЕМИУМ ОТЧЕТ):")
            print("="*80)
            print(f"\n📄 Психологический портрет - {premium_analysis_length} символов:")
            print("-" * 80)
            print(result["premium_analysis"][:500] + "..." if len(result["premium_analysis"]) > 500 else result["premium_analysis"])
            print(f"\n📄 Сильные стороны - {premium_strengths_length} символов:")
            print("-" * 80)
            print(result["premium_strengths"][:500] + "..." if len(result["premium_strengths"]) > 500 else result["premium_strengths"])
            print(f"\n📄 Зоны роста - {premium_growth_zones_length} символов:")
            print("-" * 80)
            print(result["premium_growth_zones"][:500] + "..." if len(result["premium_growth_zones"]) > 500 else result["premium_growth_zones"])
            
            # Проверяем статистику
            if "character_stats" in result:
                stats = result["character_stats"]
                total_length = stats.get("total_length", 0)
                pages_count = stats.get("pages_count", 0)
                print(f"\n📈 Статистика:")
                print(f"   - Всего символов: {total_length}")
                print(f"   - Всего страниц: {pages_count}")
                print("="*80)
                
                assert total_length > 1000, "ИИ-анализ премиум отчета слишком короткий"
                assert pages_count > 0, "Количество страниц должно быть больше 0"
        else:
            print("   ⚠️ Perplexity API отключен - ИИ-анализ не получен (ожидаемо)")
        
        # Проверяем размер файла
        size_kb = Path(self.premium_report_path).stat().st_size / 1024
        print(f"   📏 Размер премиум отчета: {size_kb:.1f} KB")
        assert size_kb > 0, "Размер премиум отчета должен быть больше 0"
        
        print(f"✅ Премиум отчет успешно сгенерирован: {self.premium_report_path}")
    
    async def test_verify_premium_report_exists(self):
        """Тест проверки наличия премиум отчета"""
        print("\n📊 Тест проверки наличия премиум отчета...")
        
        # Проверяем премиум отчет
        assert self.premium_report_path is not None, "Путь к премиум отчету не установлен"
        assert Path(self.premium_report_path).exists(), f"Премиум отчет не найден: {self.premium_report_path}"
        
        # Проверяем размер файла
        premium_size = Path(self.premium_report_path).stat().st_size
        
        print(f"   📏 Размер премиум отчета: {premium_size / 1024:.1f} KB")
        
        assert premium_size > 0, "Размер премиум отчета должен быть больше 0"
        
        print("✅ Премиум отчет существует и имеет корректный размер")
    
    async def test_check_reports_status(self):
        """Тест проверки статуса отчетов через API"""
        print("\n📊 Тест проверки статуса отчетов через API...")
        
        # Проверяем статус отчетов
        status_response = await check_user_reports_status(self.telegram_id)
        
        assert status_response["status"] == "success", "Статус должен быть success"
        assert status_response["test_completed"] == True, "Тест должен быть завершен"
        assert status_response["is_paid"] == True, "Пользователь должен быть платным"
        
        # Проверяем статус премиум отчета
        premium_status = status_response["premium_report_status"]
        assert premium_status["status"] == "ready", "Премиум отчет должен быть готов"
        
        # Проверяем доступный отчет
        available_report = status_response["available_report"]
        assert available_report["type"] == "premium", "Доступный отчет должен быть премиум"
        assert available_report["status"] == "ready", "Доступный отчет должен быть готов"
        
        print("✅ Статус отчетов корректный (премиум отчет готов)")
    
    async def run_full_pipeline(self):
        """Запуск полного теста пайплайна"""
        print("=" * 80)
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТА: Полный пайплайн с 50 вопросами (премиум отчет)")
        print("=" * 80)
        print(f"📋 Perplexity API: {'✅ Включен' if PERPLEXITY_ENABLED else '❌ Отключен'}")
        print("=" * 80)
        
        try:
            # Подготовка данных
            await self.setup_test_data()
            
            # Тесты
            await self.test_user_registration()
            await self.test_start_test()
            await self.test_answer_all_50_questions()
            await self.test_complete_test()
            await self.test_create_and_complete_payment()
            await self.test_generate_premium_report()
            await self.test_verify_premium_report_exists()
            await self.test_check_reports_status()
            
            print("\n" + "=" * 80)
            print("✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("=" * 80)
            print(f"📄 Премиум отчет: {self.premium_report_path}")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ ОШИБКА В ТЕСТЕ: {e}")
            import traceback
            traceback.print_exc()
            raise e


async def main():
    """Главная функция для запуска теста"""
    test = TestFullPipeline50Questions()
    await test.run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())

