// Telegram Web App SDK Integration (Vanilla JS)
(function() {
    'use strict';

    // Подключение Telegram Web App API
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-web-app.js';
    document.head.appendChild(script);

    script.onload = function() {
        window.TelegramWebApp = {
            tg: window.Telegram?.WebApp,
            
            init: function() {
                if (!this.tg) {
                    console.warn('Telegram WebApp API не доступен');
                    return;
                }
                
                // Инициализация Web App
                this.tg.ready();
                
                // Настройка темы
                this.setupTheme();
                
                // Настройка кнопок
                this.setupButtons();
                
                // Получение данных пользователя
                this.getUserData();
                
                console.log('Telegram WebApp инициализирован');
            },

            setupTheme: function() {
                if (!this.tg) return;
                
                // Адаптация под тему Telegram
                const root = document.documentElement;
                const theme = this.tg.themeParams;
                
                if (theme.bg_color) {
                    root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
                }
                if (theme.text_color) {
                    root.style.setProperty('--tg-theme-text-color', theme.text_color);
                }
                if (theme.hint_color) {
                    root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
                }
                if (theme.button_color) {
                    root.style.setProperty('--tg-theme-button-color', theme.button_color);
                }
                if (theme.button_text_color) {
                    root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
                }
            },

            setupButtons: function() {
                if (!this.tg) return;
                
                // Настройка главной кнопки
                this.tg.MainButton.setText('Продолжить');
                this.tg.MainButton.hide();
                
                // Настройка кнопки назад
                this.tg.BackButton.hide();
            },

            getUserData: function() {
                if (!this.tg) return null;
                
                const user = this.tg.initDataUnsafe?.user;
                if (user) {
                    console.log('Telegram User:', user);
                    return {
                        id: user.id,
                        first_name: user.first_name,
                        last_name: user.last_name,
                        username: user.username,
                        language_code: user.language_code
                    };
                }
                return null;
            },

            showMainButton: function(text, callback) {
                if (!this.tg) return;
                
                text = text || 'Продолжить';
                this.tg.MainButton.setText(text);
                this.tg.MainButton.show();
                
                if (callback) {
                    this.tg.MainButton.onClick(callback);
                }
            },

            hideMainButton: function() {
                if (!this.tg) return;
                this.tg.MainButton.hide();
            },

            showBackButton: function(callback) {
                if (!this.tg || !this.tg.BackButton) return;
                
                try {
                    this.tg.BackButton.show();
                    
                    if (callback) {
                        this.tg.BackButton.onClick(callback);
                    } else {
                        this.tg.BackButton.onClick(function() {
                            window.history.back();
                        });
                    }
                } catch (error) {
                    console.log('⬅️ BackButton не поддерживается:', error);
                }
            },

            hideBackButton: function() {
                if (!this.tg || !this.tg.BackButton) return;
                try {
                    this.tg.BackButton.hide();
                } catch (error) {
                    console.log('⬅️ BackButton не поддерживается:', error);
                }
            },

            sendData: function(data) {
                if (!this.tg) return;
                this.tg.sendData(JSON.stringify(data));
            },

            showAlert: function(message) {
                if (!this.tg) {
                    alert(message);
                    return;
                }
                this.tg.showAlert(message);
            },

            showConfirm: function(message, callback) {
                if (!this.tg) {
                    if (confirm(message)) {
                        callback(true);
                    } else {
                        callback(false);
                    }
                    return;
                }
                this.tg.showConfirm(message, callback);
            },

            hapticFeedback: function(type) {
                if (!this.tg || !this.tg.HapticFeedback) return;
                // Используем только валидные параметры для исправления WebappHapticImpactStyleInvalid
                const validTypes = ['light', 'medium', 'heavy'];
                const validType = validTypes.includes(type) ? type : 'medium';
                try {
                    this.tg.HapticFeedback.impactOccurred(validType);
                } catch (e) {
                    console.log('⚠️ Не удалось вызвать тактильную обратную связь:', e);
                }
            },

            // Централизованная функция для получения Telegram ID
            getUserId: function() {
                if (this.tg?.initDataUnsafe?.user?.id) {
                    return this.tg.initDataUnsafe.user.id;
                }
                const testId = localStorage.getItem('test_telegram_id');
                return testId ? parseInt(testId) : 123456789;
            },

            // Унифицированная обработка ошибок API
            handleError: function(error, defaultMessage = 'Произошла ошибка') {
                console.error('API Error:', error);
                const message = error?.message || error?.error || error?.detail || defaultMessage;
                this.showAlert(message);
            },

            // Проверка доступности в Telegram среде  
            isInTelegramWebApp: function() {
                return !!(window.Telegram?.WebApp || window.TelegramWebApp?.tg);
            },

            expandViewport: function() {
                if (!this.tg) return;
                this.tg.expand();
            },

            close: function() {
                if (!this.tg) {
                    window.close();
                    return;
                }
                this.tg.close();
            },

            openTelegramLink: function(url) {
                if (!this.tg) {
                    window.open(url, '_blank');
                    return;
                }
                this.tg.openTelegramLink(url);
            },

            openLink: function(url) {
                if (!this.tg) {
                    window.open(url, '_blank');
                    return;
                }
                this.tg.openLink(url);
            },

            isInTelegram: function() {
                return !!this.tg;
            }
        };

        // Автоинициализация
        window.TelegramWebApp.init();
    };
})(); 