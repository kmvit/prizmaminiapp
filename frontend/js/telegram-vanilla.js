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
            isBrowser: !window.Telegram || !window.Telegram.WebApp || window.Telegram.WebApp.platform === 'unknown',
            
            init: function() {
                console.log('🔍 Определение платформы...');
                console.log('🌐 window.Telegram:', !!window.Telegram);
                console.log('📱 this.tg:', !!this.tg);
                console.log('🖥️ isBrowser:', this.isBrowser);
                
                // Дополнительная проверка для определения Telegram Web App
                const isInTelegram = this.detectTelegramEnvironment();
                console.log('📱 Определена среда Telegram:', isInTelegram);
                
                if (!this.tg || this.isBrowser) {
                    console.warn('📱 Telegram WebApp API не доступен или это браузер');
                    console.log('🌐 Работаем в браузерном режиме');
                    return;
                }
                
                // Инициализация Web App только в Telegram
                this.tg.ready();
                
                // Настройка темы
                this.setupTheme();
                
                // Настройка кнопок
                this.setupButtons();
                
                // Получение данных пользователя
                this.getUserData();
                
                console.log('Telegram WebApp инициализирован');
            },

            // Новая функция для более точного определения среды Telegram
            detectTelegramEnvironment: function() {
                // Проверка наличия Telegram Web App API
                if (window.Telegram && window.Telegram.WebApp) {
                    return true;
                }
                
                // Проверка User-Agent
                const userAgent = navigator.userAgent.toLowerCase();
                if (userAgent.includes('telegram') || userAgent.includes('tgwebapp')) {
                    return true;
                }
                
                // Проверка URL параметров
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.has('tgWebAppData') || urlParams.has('tgWebAppStartParam')) {
                    return true;
                }
                
                // Проверка наличия Telegram-специфичных заголовков
                if (document.referrer.includes('t.me') || document.referrer.includes('telegram.org')) {
                    return true;
                }
                
                return false;
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
                // В браузере всегда используем обычный alert
                if (this.isBrowser) {
                    console.log('🌐 Браузерный режим: используем alert');
                    alert(message);
                    return;
                }
                
                // В Telegram пытаемся использовать нативный API
                try {
                    if (this.tg && this.tg.showAlert && typeof this.tg.showAlert === 'function') {
                        this.tg.showAlert(message);
                    } else {
                        console.log('📱 Telegram showAlert не поддерживается, fallback на alert');
                        alert(message);
                    }
                } catch (error) {
                    console.warn('📱 Fallback to browser alert:', error);
                    alert(message);
                }
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
                // В браузере тактильная обратная связь недоступна
                if (this.isBrowser) {
                    console.log('🌐 Браузерный режим: тактильная обратная связь не поддерживается');
                    return;
                }
                
                try {
                    if (!this.tg || !this.tg.HapticFeedback || typeof this.tg.HapticFeedback.impactOccurred !== 'function') {
                        console.log('📱 Тактильная обратная связь не поддерживается в этой версии Telegram');
                        return;
                    }
                    // Используем только валидные параметры для исправления WebappHapticImpactStyleInvalid
                    const validTypes = ['light', 'medium', 'heavy'];
                    const validType = validTypes.includes(type) ? type : 'medium';
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
                
                // Безопасный вызов showAlert без падения
                try {
                    this.showAlert(message);
                } catch (e) {
                    console.error('Ошибка в showAlert, используем console.error:', e);
                    console.error('Сообщение об ошибке:', message);
                }
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