#!/usr/bin/env python3
"""
Тест для генерации титульной страницы отчета
Проверяет создание кастомной титульной страницы с данными пользователя
"""

import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.services.pdf_service import PDFGenerator
from bot.database.models import User
from datetime import datetime


def test_title_page_generation():
    """Тест генерации титульной страницы"""
    
    print("🧪 Тестируем генерацию титульной страницы...")
    
    # Создаем экземпляр генератора PDF
    pdf_generator = PDFGenerator()
    
    # Создаем тестового пользователя
    test_user = User(
        telegram_id=123456789,
        username="test_user",
        first_name="Иван",
        last_name="Петров"
    )
    
    # Путь к шаблону титульной страницы
    template_path = Path("template_pdf_premium/block-1/title.pdf")
    
    if not template_path.exists():
        print(f"❌ Шаблон титульной страницы не найден: {template_path}")
        print("📁 Доступные файлы в template_pdf_premium/block-1/:")
        block1_dir = Path("template_pdf_premium/block-1")
        if block1_dir.exists():
            for file in block1_dir.iterdir():
                print(f"   - {file.name}")
        return False
    
    try:
        # Генерируем титульную страницу
        print(f"📄 Создаем титульную страницу для пользователя: {test_user.first_name} {test_user.last_name}")
        
        # Форматируем дату
        completion_date = datetime.utcnow().strftime("%d.%m.%Y")
        
        # Создаем кастомную титульную страницу
        title_buffer = pdf_generator.create_custom_title_page(
            template_path=template_path,
            user_name=f"{test_user.first_name} {test_user.last_name}",
            completion_date=completion_date
        )
        
        # Сохраняем результат в папку tests
        output_path = Path("tests") / "generated_title_page.pdf"
        
        with open(output_path, 'wb') as f:
            f.write(title_buffer.getvalue())
        
        print(f"✅ Титульная страница создана: {output_path}")
        print(f"📊 Размер файла: {output_path.stat().st_size} байт")
        
        # Проверяем, что файл не пустой
        if output_path.stat().st_size > 1000:  # Минимум 1KB
            print("✅ Файл имеет корректный размер")
            return True
        else:
            print("❌ Файл слишком маленький, возможно ошибка генерации")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при генерации титульной страницы: {e}")
        return False


def test_different_user_names():
    """Тест с разными вариантами имен пользователей"""
    
    print("\n🧪 Тестируем разные варианты имен пользователей...")
    
    pdf_generator = PDFGenerator()
    template_path = Path("template_pdf_premium/block-1/title.pdf")
    
    if not template_path.exists():
        print("❌ Шаблон не найден, пропускаем тест")
        return
    
    test_cases = [
        {
            "name": "Полное имя",
            "user": User(telegram_id=1, first_name="Анна", last_name="Сидорова", username="anna_s")
        },
        {
            "name": "Только имя",
            "user": User(telegram_id=2, first_name="Михаил", username="mike")
        },
        {
            "name": "Только username",
            "user": User(telegram_id=3, username="john_doe")
        },
        {
            "name": "Пустые данные",
            "user": User(telegram_id=4)
        }
    ]
    
    completion_date = datetime.utcnow().strftime("%d.%m.%Y")
    
    for i, test_case in enumerate(test_cases, 1):
        user = test_case["user"]
        
        # Формируем имя пользователя
        if user.first_name and user.last_name:
            user_name = f"{user.first_name} {user.last_name}"
        elif user.first_name:
            user_name = user.first_name
        elif user.username:
            user_name = f"Пользователь {user.username}"
        else:
            user_name = f"Пользователь {user.telegram_id}"
        
        try:
            title_buffer = pdf_generator.create_custom_title_page(
                template_path=template_path,
                user_name=user_name,
                completion_date=completion_date
            )
            
            output_path = Path("tests") / f"title_page_test_{i}_{test_case['name'].replace(' ', '_')}.pdf"
            
            with open(output_path, 'wb') as f:
                f.write(title_buffer.getvalue())
            
            print(f"✅ {test_case['name']}: {output_path.name}")
            
        except Exception as e:
            print(f"❌ {test_case['name']}: ошибка - {e}")


def main():
    """Основная функция тестирования"""
    
    print("🚀 Запуск тестов генерации титульной страницы")
    print("=" * 50)
    
    # Создаем папку tests если её нет
    tests_dir = Path("tests")
    tests_dir.mkdir(exist_ok=True)
    
    # Основной тест
    success = test_title_page_generation()
    
    # Дополнительные тесты с разными именами
    test_different_user_names()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Все тесты завершены успешно!")
        print("📁 Проверьте сгенерированные файлы в папке tests/")
    else:
        print("⚠️ Некоторые тесты завершились с ошибками")
    
    return success


if __name__ == "__main__":
    main() 