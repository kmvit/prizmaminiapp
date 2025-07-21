#!/usr/bin/env python3
"""
Комплексный тест для тестирования ИИ и генерации премиум отчета в PDF
Тестирует:
1. Работу с Perplexity API
2. Генерацию премиум анализа
3. Создание PDF отчета
4. Оптимизацию запросов к ИИ
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import time

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from bot.config import settings, PERPLEXITY_ENABLED
from bot.database.models import User, Question, Answer
from bot.services.perplexity import PerplexityAIService, AIAnalysisService
from bot.services.pdf_service import ReportGenerator
from bot.services.database_service import db_service

class TestUser:
    """Тестовый класс пользователя"""
    def __init__(self, telegram_id: int = 12345, first_name: str = "Тестовый", last_name: str = "Пользователь"):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = datetime.now()

class TestQuestion:
    """Тестовый класс вопроса"""
    def __init__(self, id: int, order_number: int, text: str, question_type: str = "FREE"):
        self.id = id
        self.order_number = order_number
        self.text = text
        self.type = question_type

class TestAnswer:
    """Тестовый класс ответа"""
    def __init__(self, question_id: int, text_answer: str, voice_answer: str = None):
        self.question_id = question_id
        self.text_answer = text_answer
        self.voice_answer = voice_answer
        self.created_at = datetime.now()

class PremiumReportTester:
    """Класс для тестирования генерации премиум отчетов"""
    
    def __init__(self):
        self.ai_service = AIAnalysisService()
        self.report_generator = ReportGenerator()
        self.test_results = {}
        
    def load_test_data(self, report_type: str = "premium") -> tuple:
        """Загружает тестовые данные из JSON файла (ТОЛЬКО для премиум отчета)"""
        
        questions_file = Path("data/questions.json")
        if not questions_file.exists():
            raise FileNotFoundError(f"Файл с вопросами не найден: {questions_file}")
            
        with open(questions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        questions = []
        answers = []
        
        for item in data["questions"]:
            # Создаем тестовый вопрос
            question = TestQuestion(
                id=item["order_number"],
                order_number=item["order_number"],
                text=item["text"],
                question_type=item["type"]
            )
            questions.append(question)
            
            # Создаем тестовый ответ, если есть
            if "answer" in item and item["answer"]:
                answer = TestAnswer(
                    question_id=item["order_number"],
                    text_answer=item["answer"]
                )
                answers.append(answer)
        
        # ТЕСТИРУЕМ ТОЛЬКО ПРЕМИУМ ОТЧЕТ - берем все вопросы
        if report_type != "premium":
            print(f"⚠️ Тест настроен только для премиум отчета, игнорируем тип '{report_type}'")
            
        print(f"📊 Загружено {len(questions)} вопросов и {len(answers)} ответов для ПРЕМИУМ отчета")
        
        return questions, answers
    
    async def test_perplexity_api_connection(self) -> bool:
        """Тестирует подключение к Perplexity API"""
        
        print("🔌 === ТЕСТ ПОДКЛЮЧЕНИЯ К PERPLEXITY API ===")
        
        if not PERPLEXITY_ENABLED:
            print("⚠️ Perplexity API отключен в конфигурации")
            return False
            
        if not settings.PERPLEXITY_API_KEY:
            print("❌ API ключ Perplexity не найден")
            return False
            
        try:
            # Создаем простой тестовый запрос
            ai_service = PerplexityAIService()
            
            test_messages = [
                {
                    "role": "system",
                    "content": "Ты - помощник для тестирования. Ответь кратко: 'API работает'"
                },
                {
                    "role": "user", 
                    "content": "Проверь подключение"
                }
            ]
            
            print("🔄 Отправляем тестовый запрос к API...")
            start_time = time.time()
            
            result = await ai_service._make_api_request(test_messages, is_premium=False)
            
            elapsed = time.time() - start_time
            print(f"✅ API ответ получен за {elapsed:.2f} секунд")
            print(f"📝 Ответ: {result['content'][:100]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения к API: {e}")
            return False
    
    async def test_premium_analysis_generation(self, user: TestUser, questions: List[TestQuestion], answers: List[TestAnswer]) -> Dict:
        """Тестирует генерацию ТОЛЬКО ПРЕМИУМ анализа (без бесплатного)"""
        
        print("\n🧠 === ТЕСТ ГЕНЕРАЦИИ ПРЕМИУМ АНАЛИЗА ===")
        
        try:
            print(f"👤 Пользователь: {user.first_name} {user.last_name} (ID: {user.telegram_id})")
            print(f"📝 Количество вопросов: {len(questions)}")
            print(f"💬 Количество ответов: {len(answers)}")
            
            # Статистика по типам вопросов
            free_questions = [q for q in questions if q.type == "FREE"]
            paid_questions = [q for q in questions if q.type == "PAID"]
            
            print(f"   🆓 Бесплатных вопросов: {len(free_questions)}")
            print(f"   💰 Платных вопросов: {len(paid_questions)}")
            
            # Проверяем, что есть платные вопросы
            if len(paid_questions) == 0:
                print("⚠️ Нет платных вопросов для премиум анализа!")
                return {"success": False, "error": "Нет платных вопросов"}
            
            # Генерируем ТОЛЬКО премиум анализ
            print(f"\n🤖 Начинаем генерацию ПРЕМИУМ анализа (без бесплатного)...")
            start_time = time.time()
            
            analysis_result = await self.ai_service.generate_premium_report(
                user=user,
                questions=questions,
                answers=answers
            )
            
            generation_time = time.time() - start_time
            print(f"⏱️ Время генерации премиум анализа: {generation_time:.2f} секунд")
            
            if analysis_result["success"]:
                print("✅ Премиум анализ успешно сгенерирован!")
                
                # Анализируем результат
                self._analyze_analysis_result(analysis_result)
                
                return analysis_result
            else:
                print("❌ Ошибка при генерации премиум анализа!")
                print(f"   Причина: {analysis_result.get('error', 'Неизвестная ошибка')}")
                return analysis_result
                
        except Exception as e:
            print(f"💥 Критическая ошибка при генерации премиум анализа: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_analysis_result(self, analysis_result: Dict):
        """Анализирует результат генерации анализа"""
        
        print(f"\n📊 АНАЛИЗ РЕЗУЛЬТАТА:")
        
        # Проверяем наличие всех разделов
        expected_sections = [
            "premium_analysis", "premium_strengths", "premium_growth_zones",
            "premium_compensation", "premium_interaction", "premium_prognosis",
            "premium_practical", "premium_conclusion", "premium_appendix"
        ]
        
        total_chars = 0
        sections_found = 0
        
        for section_key in expected_sections:
            content = analysis_result.get(section_key, "")
            section_len = len(content)
            total_chars += section_len
            
            if section_len > 0:
                sections_found += 1
                print(f"   ✅ {section_key}: {section_len} символов")
            else:
                print(f"   ❌ {section_key}: отсутствует")
        
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   📄 Разделов найдено: {sections_found}/{len(expected_sections)}")
        print(f"   📝 Общий объем: {total_chars} символов")
        print(f"   📊 Средний объем раздела: {total_chars // sections_found if sections_found > 0 else 0} символов")
        
        # Статистика использования API
        usage_stats = analysis_result.get("usage", {})
        api_calls = usage_stats.get("total_api_calls", "неизвестно")
        pages_generated = usage_stats.get("pages_generated", "неизвестно")
        optimization_ratio = usage_stats.get("optimization_ratio", "неизвестно")
        
        print(f"\n⚡ СТАТИСТИКА API:")
        print(f"   📞 Всего запросов к ИИ: {api_calls}")
        print(f"   📄 Страниц сгенерировано: {pages_generated}")
        print(f"   🎯 Экономия запросов: {optimization_ratio}")
    
    async def test_pdf_generation(self, user: TestUser, analysis_result: Dict) -> Optional[str]:
        """Тестирует генерацию PDF отчета"""
        
        print(f"\n📄 === ТЕСТ ГЕНЕРАЦИИ PDF ОТЧЕТА ===")
        
        try:
            print(f"🔄 Начинаем генерацию PDF отчета...")
            start_time = time.time()
            
            pdf_path = self.report_generator.create_premium_pdf_report(
                user=user,
                analysis_result=analysis_result
            )
            
            pdf_generation_time = time.time() - start_time
            print(f"⏱️ Время генерации PDF: {pdf_generation_time:.2f} секунд")
            
            if pdf_path and Path(pdf_path).exists():
                file_size = Path(pdf_path).stat().st_size / 1024  # KB
                print(f"✅ PDF отчет успешно создан!")
                print(f"   📁 Путь: {pdf_path}")
                print(f"   📦 Размер: {file_size:.1f} KB")
                
                # Проверяем размер файла
                if file_size > 100:  # Больше 100 KB
                    print(f"   ✅ Размер файла в норме (>100 KB)")
                else:
                    print(f"   ⚠️ Размер файла подозрительно мал (<100 KB)")
                
                return pdf_path
            else:
                print("❌ Ошибка при создании PDF отчета!")
                return None
                
        except Exception as e:
            print(f"💥 Критическая ошибка при генерации PDF: {e}")
            return None
    
    async def test_full_workflow(self, test_type: str = "premium") -> Dict:
        """Тестирует полный workflow: загрузка данных → ПРЕМИУМ анализ → PDF (БЕЗ бесплатного отчета)"""
        
        print("🚀 === ПОЛНЫЙ ТЕСТ WORKFLOW (ТОЛЬКО ПРЕМИУМ) ===")
        print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        workflow_result = {
            "success": False,
            "steps": {},
            "total_time": 0,
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            # Шаг 1: Проверка API
            print(f"\n🔌 Шаг 1: Проверка Perplexity API...")
            api_ok = await self.test_perplexity_api_connection()
            workflow_result["steps"]["api_check"] = api_ok
            
            if not api_ok:
                workflow_result["errors"].append("API недоступен")
                print("⚠️ Продолжаем тест без API...")
            
            # Шаг 2: Загрузка данных (ТОЛЬКО для премиум отчета)
            print(f"\n📊 Шаг 2: Загрузка тестовых данных для ПРЕМИУМ отчета...")
            questions, answers = self.load_test_data("premium")  # Принудительно премиум
            workflow_result["steps"]["data_loading"] = True
            workflow_result["steps"]["questions_count"] = len(questions)
            workflow_result["steps"]["answers_count"] = len(answers)
            
            # Шаг 3: Создание тестового пользователя
            user = TestUser(
                telegram_id=999999,
                first_name="Тестовый",
                last_name="Пользователь"
            )
            
            # Шаг 4: Генерация ПРЕМИУМ анализа (БЕЗ бесплатного)
            print(f"\n🧠 Шаг 3: Генерация ПРЕМИУМ анализа (без бесплатного)...")
            analysis_result = await self.test_premium_analysis_generation(user, questions, answers)
            workflow_result["steps"]["analysis_generation"] = analysis_result.get("success", False)
            
            if not analysis_result.get("success"):
                workflow_result["errors"].append(f"Ошибка премиум анализа: {analysis_result.get('error', 'Неизвестная ошибка')}")
            
            # Шаг 5: Генерация ПРЕМИУМ PDF
            if analysis_result.get("success"):
                print(f"\n📄 Шаг 4: Генерация ПРЕМИУМ PDF отчета...")
                pdf_path = await self.test_pdf_generation(user, analysis_result)
                workflow_result["steps"]["pdf_generation"] = pdf_path is not None
                
                if pdf_path:
                    workflow_result["steps"]["pdf_path"] = pdf_path
                    workflow_result["steps"]["pdf_size"] = Path(pdf_path).stat().st_size / 1024
                else:
                    workflow_result["errors"].append("Ошибка генерации премиум PDF")
            
            # Итоги
            total_time = time.time() - start_time
            workflow_result["total_time"] = total_time
            
            success_steps = sum(1 for step, result in workflow_result["steps"].items() 
                              if isinstance(result, bool) and result)
            total_steps = sum(1 for step, result in workflow_result["steps"].items() 
                            if isinstance(result, bool))
            
            workflow_result["success"] = success_steps == total_steps and len(workflow_result["errors"]) == 0
            
            print(f"\n🏁 === ИТОГИ WORKFLOW (ПРЕМИУМ) ===")
            print(f"✅ Успешных шагов: {success_steps}/{total_steps}")
            print(f"⏱️ Общее время: {total_time:.2f} секунд")
            print(f"🎯 Результат: {'УСПЕХ' if workflow_result['success'] else 'НЕУДАЧА'}")
            print(f"💎 Тип отчета: ПРЕМИУМ (без бесплатного)")
            
            if workflow_result["errors"]:
                print(f"❌ Ошибки:")
                for error in workflow_result["errors"]:
                    print(f"   • {error}")
            
            return workflow_result
            
        except Exception as e:
            workflow_result["errors"].append(f"Критическая ошибка: {str(e)}")
            print(f"💥 Критическая ошибка в workflow: {e}")
            return workflow_result
    
    async def run_performance_test(self, iterations: int = 3) -> Dict:
        """Запускает тест производительности с несколькими итерациями (ТОЛЬКО ПРЕМИУМ)"""
        
        print(f"\n⚡ === ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ ПРЕМИУМ ОТЧЕТА ({iterations} итераций) ===")
        
        performance_results = {
            "iterations": [],
            "average_time": 0,
            "success_rate": 0
        }
        
        success_count = 0
        
        for i in range(iterations):
            print(f"\n🔄 Итерация {i + 1}/{iterations} (ПРЕМИУМ)")
            
            try:
                result = await self.test_full_workflow("premium")  # Принудительно премиум
                performance_results["iterations"].append(result)
                
                if result["success"]:
                    success_count += 1
                    print(f"✅ Итерация {i + 1} - УСПЕХ (ПРЕМИУМ)")
                else:
                    print(f"❌ Итерация {i + 1} - НЕУДАЧА (ПРЕМИУМ)")
                    
            except Exception as e:
                print(f"💥 Итерация {i + 1} - КРИТИЧЕСКАЯ ОШИБКА (ПРЕМИУМ): {e}")
                performance_results["iterations"].append({
                    "success": False,
                    "error": str(e),
                    "total_time": 0
                })
        
        # Вычисляем статистику
        successful_results = [r for r in performance_results["iterations"] if r.get("success")]
        
        if successful_results:
            avg_time = sum(r["total_time"] for r in successful_results) / len(successful_results)
            performance_results["average_time"] = avg_time
        
        performance_results["success_rate"] = success_count / iterations
        
        print(f"\n📊 СТАТИСТИКА ПРОИЗВОДИТЕЛЬНОСТИ (ПРЕМИУМ):")
        print(f"   ✅ Успешных итераций: {success_count}/{iterations}")
        print(f"   📈 Процент успеха: {performance_results['success_rate']*100:.1f}%")
        print(f"   ⏱️ Среднее время: {performance_results['average_time']:.2f} секунд")
        print(f"   💎 Тип отчета: ПРЕМИУМ (без бесплатного)")
        
        return performance_results

async def main():
    """Главная функция для запуска тестов (ТОЛЬКО ПРЕМИУМ ОТЧЕТ)"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Тестирование ИИ и генерации ПРЕМИУМ отчетов (без бесплатного)")
    parser.add_argument(
        "--type", 
        choices=["api", "analysis", "pdf", "workflow", "performance"], 
        default="workflow",
        help="Тип теста (default: workflow) - ВСЕ ТЕСТЫ ТОЛЬКО ДЛЯ ПРЕМИУМ ОТЧЕТА"
    )
    parser.add_argument(
        "--iterations", 
        type=int, 
        default=1,
        help="Количество итераций для теста производительности (default: 1)"
    )
    
    args = parser.parse_args()
    
    tester = PremiumReportTester()
    
    print("💎 === ТЕСТ НАСТРОЕН ТОЛЬКО НА ПРЕМИУМ ОТЧЕТ ===")
    
    if args.type == "api":
        await tester.test_perplexity_api_connection()
    elif args.type == "analysis":
        questions, answers = tester.load_test_data("premium")  # Принудительно премиум
        user = TestUser(telegram_id=999999, first_name="Тест", last_name="Премиум")
        await tester.test_premium_analysis_generation(user, questions, answers)
    elif args.type == "pdf":
        # Создаем тестовый анализ для ПРЕМИУМ PDF
        questions, answers = tester.load_test_data("premium")  # Принудительно премиум
        user = TestUser(telegram_id=999999, first_name="Тест", last_name="Премиум")
        analysis_result = await tester.test_premium_analysis_generation(user, questions, answers)
        if analysis_result.get("success"):
            await tester.test_pdf_generation(user, analysis_result)
    elif args.type == "workflow":
        await tester.test_full_workflow("premium")  # Принудительно премиум
    elif args.type == "performance":
        await tester.run_performance_test(args.iterations)  # Принудительно премиум

if __name__ == "__main__":
    asyncio.run(main()) 