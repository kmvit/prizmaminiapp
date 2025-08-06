#!/usr/bin/env python3
"""
Скрипт для запуска тестов пользовательских путей
- Бесплатный путь пользователя
- Платный путь пользователя
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импорта модулей
sys.path.append(str(Path(__file__).parent.parent))

from test_free_user_journey import TestFreeUserJourney
from test_premium_user_journey import TestPremiumUserJourney

async def run_free_user_test():
    """Запуск теста бесплатного пользователя"""
    print("\n" + "=" * 80)
    print("🎯 ЗАПУСК ТЕСТА БЕСПЛАТНОГО ПОЛЬЗОВАТЕЛЯ")
    print("=" * 80)
    
    try:
        test = TestFreeUserJourney()
        await test.run_full_journey()
        return True
    except Exception as e:
        print(f"❌ ТЕСТ БЕСПЛАТНОГО ПОЛЬЗОВАТЕЛЯ ПРОВАЛЕН: {e}")
        return False

async def run_premium_user_test():
    """Запуск теста платного пользователя"""
    print("\n" + "=" * 80)
    print("🎯 ЗАПУСК ТЕСТА ПЛАТНОГО ПОЛЬЗОВАТЕЛЯ")
    print("=" * 80)
    
    try:
        test = TestPremiumUserJourney()
        await test.run_full_journey()
        return True
    except Exception as e:
        print(f"❌ ТЕСТ ПЛАТНОГО ПОЛЬЗОВАТЕЛЯ ПРОВАЛЕН: {e}")
        return False

async def main():
    """Главная функция для запуска всех тестов"""
    print("🚀 ЗАПУСК КОМПЛЕКСНЫХ ТЕСТОВ ПОЛЬЗОВАТЕЛЬСКИХ ПУТЕЙ")
    print("=" * 80)
    
    results = []
    
    # Запускаем тест бесплатного пользователя
    free_result = await run_free_user_test()
    results.append(("Бесплатный пользователь", free_result))
    
    # Запускаем тест платного пользователя
    premium_result = await run_premium_user_test()
    results.append(("Платный пользователь", premium_result))
    
    # Выводим итоговые результаты
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Система работает корректно")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        print("🔧 Требуется доработка системы")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 