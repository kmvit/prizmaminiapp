#!/usr/bin/env python3
"""
Скрипт для исправления значений enum в базе данных
"""

import sqlite3
from pathlib import Path

def fix_enum_values():
    """Исправить значения enum в базе данных"""
    
    db_path = Path("data/bot.db")
    
    if not db_path.exists():
        print("❌ База данных не найдена.")
        return False
    
    print(f"🔧 Исправляем значения enum в базе данных: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Обновляем значения enum для ReportGenerationStatus
        enum_updates = [
            ("pending", "PENDING"),
            ("processing", "PROCESSING"),
            ("completed", "COMPLETED"),
            ("failed", "FAILED")
        ]
        
        for old_value, new_value in enum_updates:
            # Обновляем free_report_status
            cursor.execute(
                "UPDATE users SET free_report_status = ? WHERE free_report_status = ?",
                (new_value, old_value)
            )
            updated_free = cursor.rowcount
            
            # Обновляем premium_report_status
            cursor.execute(
                "UPDATE users SET premium_report_status = ? WHERE premium_report_status = ?",
                (new_value, old_value)
            )
            updated_premium = cursor.rowcount
            
            if updated_free > 0 or updated_premium > 0:
                print(f"✅ Обновлено {updated_free + updated_premium} записей: {old_value} -> {new_value}")
        
        # Сохраняем изменения
        conn.commit()
        print("✅ Исправление значений enum завершено!")
        
        # Показываем текущие значения
        cursor.execute("SELECT DISTINCT free_report_status, premium_report_status FROM users")
        current_values = cursor.fetchall()
        print("\n📋 Текущие значения в базе данных:")
        for free_status, premium_status in current_values:
            print(f"  - free_report_status: {free_status}")
            print(f"  - premium_report_status: {premium_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении значений enum: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_enum_values() 