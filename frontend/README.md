# PRIZMA - Telegram Mini App

Психологический опросник в виде Telegram Mini App с интеграцией ИИ анализа личности.

## 🚀 Быстрый старт

### 1. Запуск локального сервера

```bash
# Запуск HTTP сервера для тестирования
python3 server.py
```

Сервер будет доступен по адресу: `http://localhost:8000`

### 2. Настройка ngrok для тестирования в Telegram

```bash
# Установите ngrok (если не установлен)
# brew install ngrok  # для macOS
# или скачайте с https://ngrok.com/

# Запустите туннель
ngrok http 8000
```

Скопируйте HTTPS URL из ngrok (например: `https://abc123.ngrok.io`)

### 3. Создание Telegram бота

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Выполните команды:
   ```
   /newbot
   Выберите имя: PRIZMA Psychology Bot
   Выберите username: prizma_psychology_bot
   ```
3. Сохраните токен бота

### 4. Настройка Web App

1. Отправьте `/newapp` в [@BotFather](https://t.me/BotFather)
2. Выберите вашего бота
3. Введите:
   - **Title**: PRIZMA - Анализ личности
   - **Description**: Пройдите психологический опрос и получите ИИ анализ вашей личности
   - **Photo**: Загрузите изображение 640x360px
   - **Web App URL**: Ваш ngrok URL (например: `https://abc123.ngrok.io`)

## 📁 Структура проекта

```
frontend/prizma/
├── index.html              # Главная страница
├── steps.html              # Описание шагов
├── login.html              # Форма данных пользователя  
├── question.html           # Страница вопросов
├── loading.html            # Экран загрузки
├── answers.html            # Результаты
├── price.html              # Тарифы
├── complete-payment.html   # Успешная оплата
├── uncomplete-payment.html # Неуспешная оплата
├── download.html           # Скачивание отчета
├── css/
│   └── main.css           # Основные стили
├── js/
│   ├── config.js          # Конфигурация приложения
│   ├── telegram-vanilla.js # Telegram Web App SDK
│   ├── main-telegram.js   # Основная логика с Telegram
│   ├── main.js            # Оригинальная логика
│   ├── jquery.min.js      # jQuery
│   └── jquery-ui.min.js   # jQuery UI
├── images/                # Изображения и иконки
├── fonts/                 # Шрифты
└── server.py             # HTTP сервер для разработки
```

## ⚙️ Конфигурация

### Файл `js/config.js`

Основные настройки приложения:

```javascript
window.AppConfig = {
    api: {
        baseUrl: 'http://localhost:8080/api', // URL backend API
        // ...
    },
    telegram: {
        webAppUrl: 'https://your-domain.com', // Ваш домен
        // ...
    },
    survey: {
        totalQuestions: 15, // Количество вопросов
        // ...
    }
    // ...
};
```

### Основные параметры для изменения:

1. **`api.baseUrl`** - URL вашего backend API
2. **`telegram.webAppUrl`** - URL вашего приложения  
3. **`survey.questions`** - Массив вопросов для опроса
4. **`payment.prices`** - Цены на тарифы
5. **`development.mockAPI`** - Включить/выключить mock API

## 🔧 Интеграция с Backend

### API Endpoints

Приложение ожидает следующие endpoints:

```
POST /api/user/profile      # Сохранение профиля пользователя
POST /api/user/answers      # Сохранение ответов
GET  /api/user/report       # Генерация отчета
POST /api/payment/create    # Создание платежа
GET  /api/payment/status    # Проверка статуса платежа
```

### Формат данных

**Профиль пользователя:**
```json
{
    "name": "Имя",
    "age": 25,
    "gender": "male",
    "telegramUser": {
        "id": 123456789,
        "first_name": "Имя",
        "username": "username"
    }
}
```

**Ответы пользователя:**
```json
{
    "answers": [
        {
            "question": 1,
            "answer": "Текст ответа...",
            "timestamp": "2024-01-01T12:00:00.000Z"
        }
    ]
}
```

## 🎨 Кастомизация

### Изменение вопросов

Отредактируйте массив `AppConfig.survey.questions` в файле `js/config.js`

### Изменение стилей

Основные стили находятся в файле `css/main.css`. Приложение поддерживает:
- Градиенты и анимации
- Адаптивный дизайн
- Telegram theme colors
- Тактильную обратную связь

### Добавление новых страниц

1. Создайте HTML файл
2. Добавьте интеграцию:
   ```html
   <script src="js/config.js"></script>
   <script src="js/telegram-vanilla.js"></script>
   ```
3. Добавьте обработчик в `main-telegram.js`

## 🧪 Тестирование

### Локальное тестирование

1. Запустите `python3 server.py`
2. Откройте `http://localhost:8000` в браузере
3. Используйте Developer Tools для имитации Telegram

### Тестирование в Telegram

1. Настройте ngrok: `ngrok http 8000`
2. Обновите Web App URL в BotFather
3. Откройте бота в Telegram и запустите `/start`

### Mock API

Для тестирования без backend установите в `config.js`:
```javascript
development: {
    mockAPI: true
}
```

## 🚀 Деплой в продакшн

### 1. Настройка сервера

- Загрузите файлы на ваш сервер
- Настройте HTTPS (обязательно для Telegram)
- Настройте веб-сервер (nginx/apache)

### 2. Обновление конфигурации

```javascript
// В production установите:
window.AppConfig = {
    api: {
        baseUrl: 'https://your-api.com/api'
    },
    telegram: {
        webAppUrl: 'https://your-domain.com'
    },
    development: {
        mockAPI: false,
        enableLogging: false
    }
};
```

### 3. Обновление Bot

Отправьте новый URL в [@BotFather](https://t.me/BotFather):
```
/editapp
Выберите бота
Выберите приложение
Edit Web App URL
https://your-domain.com
```

## 🔐 Безопасность

- ✅ Все данные передаются через HTTPS
- ✅ Telegram init data валидируется на backend
- ✅ Локальные данные хранятся в localStorage
- ✅ API ключи не хранятся в frontend

## 📱 Особенности Telegram Mini App

### Поддерживаемые функции:
- ✅ Основные кнопки (MainButton, BackButton)
- ✅ Тактильная обратная связь (HapticFeedback)
- ✅ Темы Telegram (ThemeParams)
- ✅ Получение данных пользователя
- ✅ Отправка данных в бота
- ✅ Управление viewport

### Ограничения:
- ❌ Голосовые записи требуют дополнительной интеграции
- ❌ Файлы загружаются через бота, не напрямую
- ❌ Некоторые браузерные API недоступны

## 🆘 Устранение неполадок

### Приложение не загружается в Telegram
1. Проверьте HTTPS подключение
2. Убедитесь что URL доступен извне
3. Проверьте консоль браузера на ошибки

### Кнопки Telegram не работают
1. Проверьте что `telegram-vanilla.js` загружается
2. Убедитесь что `TelegramWebApp.init()` вызывается
3. Проверьте наличие `window.Telegram.WebApp`

### API не работает
1. Проверьте настройки CORS на backend
2. Убедитесь что `X-Telegram-Init-Data` передается
3. Включите `mockAPI: true` для тестирования

## 📞 Поддержка

При возникновении проблем:
1. Проверьте консоль браузера
2. Убедитесь что все файлы загрузились
3. Проверьте настройки в `config.js`
4. Протестируйте с включенным `mockAPI` 