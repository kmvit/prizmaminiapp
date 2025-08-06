/**
 * Telegram Web App API Utilities
 * Утилиты для работы с Telegram Web App API
 */

(function() {
    'use strict';

    // Подключение Telegram Web App API
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-web-app.js';
    document.head.appendChild(script);

    script.onload = function() {
        window.TelegramWebApp = {
            // Основные свойства
            tg: window.Telegram?.WebApp,
            isBrowser: !window.Telegram || !window.Telegram.WebApp || window.Telegram.WebApp.platform === 'unknown',
            
            /**
             * Инициализация Telegram Web App
             */
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
                
                console.log('✅ Telegram WebApp инициализирован');
            },

            /**
             * Определение среды Telegram
             * @returns {boolean} true если в Telegram Web App
             */
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

            /**
             * Настройка темы Telegram
             */
            setupTheme: function() {
                if (!this.tg) return;
                
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

            /**
             * Настройка кнопок Telegram
             */
            setupButtons: function() {
                if (!this.tg) return;
                
                // Настройка главной кнопки
                this.tg.MainButton.setText('Продолжить');
                this.tg.MainButton.hide();
                
                // Настройка кнопки назад
                this.tg.BackButton.hide();
            },

            /**
             * Получение данных пользователя
             * @returns {Object|null} Данные пользователя или null
             */
            getUserData: function() {
                if (!this.tg) return null;
                
                const user = this.tg.initDataUnsafe?.user;
                if (user) {
                    console.log('👤 Telegram User:', user);
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

            /**
             * Показать главную кнопку
             * @param {string} text - Текст кнопки
             * @param {Function} callback - Обработчик клика
             */
            showMainButton: function(text, callback) {
                if (!this.tg) return;
                
                text = text || 'Продолжить';
                this.tg.MainButton.setText(text);
                this.tg.MainButton.show();
                
                if (callback) {
                    this.tg.MainButton.onClick(callback);
                }
            },

            /**
             * Скрыть главную кнопку
             */
            hideMainButton: function() {
                if (!this.tg) return;
                this.tg.MainButton.hide();
            },

            /**
             * Показать кнопку назад
             * @param {Function} callback - Обработчик клика
             */
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

            /**
             * Скрыть кнопку назад
             */
            hideBackButton: function() {
                if (!this.tg || !this.tg.BackButton) return;
                try {
                    this.tg.BackButton.hide();
                } catch (error) {
                    console.log('⬅️ BackButton не поддерживается:', error);
                }
            },

            /**
             * Отправить данные в Telegram
             * @param {Object} data - Данные для отправки
             */
            sendData: function(data) {
                if (!this.tg) return;
                this.tg.sendData(JSON.stringify(data));
            },

            /**
             * Показать алерт
             * @param {string} message - Сообщение
             */
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

            /**
             * Показать подтверждение
             * @param {string} message - Сообщение
             * @param {Function} callback - Обработчик результата
             */
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

            /**
             * Тактильная обратная связь
             * @param {string} type - Тип обратной связи ('light', 'medium', 'heavy')
             */
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

            /**
             * Получить ID пользователя
             * @returns {number} ID пользователя
             */
            getUserId: function() {
                if (this.tg?.initDataUnsafe?.user?.id) {
                    return this.tg.initDataUnsafe.user.id;
                }
                const testId = localStorage.getItem('test_telegram_id');
                return testId ? parseInt(testId) : 123456789;
            },

            /**
             * Обработка ошибок API
             * @param {Error} error - Ошибка
             * @param {string} defaultMessage - Сообщение по умолчанию
             */
            handleError: function(error, defaultMessage = 'Произошла ошибка') {
                console.error('❌ API Error:', error);
                const message = error?.message || error?.error || error?.detail || defaultMessage;
                
                // Безопасный вызов showAlert без падения
                try {
                    this.showAlert(message);
                } catch (e) {
                    console.error('Ошибка в showAlert, используем console.error:', e);
                    console.error('Сообщение об ошибке:', message);
                }
            },

            /**
             * Проверка доступности в Telegram среде
             * @returns {boolean} true если в Telegram Web App
             */
            isInTelegramWebApp: function() {
                return !!(window.Telegram?.WebApp || window.TelegramWebApp?.tg);
            },

            /**
             * Расширить viewport
             */
            expandViewport: function() {
                if (!this.tg) return;
                this.tg.expand();
            },

            /**
             * Закрыть приложение
             */
            close: function() {
                if (!this.tg) {
                    window.close();
                    return;
                }
                this.tg.close();
            },

            /**
             * Открыть ссылку в Telegram
             * @param {string} url - URL для открытия
             */
            openTelegramLink: function(url) {
                if (!this.tg) {
                    window.open(url, '_blank');
                    return;
                }
                this.tg.openTelegramLink(url);
            },

            /**
             * Открыть ссылку
             * @param {string} url - URL для открытия
             */
            openLink: function(url) {
                if (!this.tg) {
                    window.open(url, '_blank');
                    return;
                }
                this.tg.openLink(url);
            },

            /**
             * Проверка нахождения в Telegram
             * @returns {boolean} true если в Telegram
             */
            isInTelegram: function() {
                return !!this.tg;
            }
        };

        // Автоинициализация
        window.TelegramWebApp.init();
    };
})(); 