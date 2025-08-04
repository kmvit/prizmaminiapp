#!/bin/bash

# Скрипт для обнуления отчетов и оплаты у пользователей
echo "🔄 Сброс пользователей..."

# Проверяем существование базы данных
if [ ! -f "bot/database/database.db" ]; then
    echo "❌ База данных не найдена: bot/database/database.db"
    exit 1
fi

# Запускаем SQLite скрипт
sqlite3 bot/database/database.db < reset_users.sql

echo "✅ Сброс завершен!" 