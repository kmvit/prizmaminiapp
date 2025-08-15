/**
 * Страница цен (price.html)
 * Инициализация и логика страницы цен
 */

'use strict';

window.PricePage = {
    /**
     * Инициализация страницы цен
     */
    init() {
        console.log('💰 Инициализация страницы цен');
        
        // Сначала проверяем статус платежа - если оплачен, перенаправляем
        this.checkPaymentStatusOnLoad().then(() => {
            // Только если не перенаправлены, настраиваем UI и обработчики
            this.setupTelegramUI();
            this.setupEventHandlers();
            // Обновляем текст кнопки в зависимости от статуса пользователя
            this.updateButtonText();
        });
    },

    /**
     * Настройка Telegram UI для страницы цен
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showBackButton(() => {
                window.location.href = 'steps.html';
            });
            window.TelegramWebApp.hideMainButton();
        }
    },

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        // Обработчик для кнопки бесплатного отчета
        $('#startFreeReport').on('click', (e) => {
            e.preventDefault();
            console.log('🆓 Запуск бесплатного отчета');
            this.startFreeReport();
        });

        // Обработчик для кнопки премиум отчета
        $('#startPremiumPayment').on('click', (e) => {
            e.preventDefault();
            console.log('💎 Запуск премиум отчета');
            this.startPremiumPayment();
        });
    },

    /**
     * Обновление текста кнопки в зависимости от статуса пользователя
     */
    async updateButtonText() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            // Получаем профиль пользователя
            const profile = await ApiClient.getUserProfile(telegramId);
            console.log('👤 Профиль пользователя:', profile);
            
            if (profile && profile.payment_status === 'completed') {
                // Пользователь оплатил, проверяем прогресс
                const progress = await ApiClient.getUserProgress(telegramId);
                console.log('📊 Прогресс пользователя:', progress);
                
                let buttonText = 'Начать';
                
                if (progress && progress.progress && progress.progress.answered > 0) {
                    buttonText = 'Продолжить';
                }
                
                // Обновляем текст кнопки
                $('#startPremiumPayment').text(buttonText);
                console.log(`✅ Кнопка обновлена: "${buttonText}"`);
            } else {
                // Пользователь не оплатил, оставляем "Попробовать"
                $('#startPremiumPayment').text('Попробовать');
                console.log('✅ Кнопка оставлена: "Попробовать"');
            }
            
        } catch (error) {
            console.error('❌ Ошибка при обновлении текста кнопки:', error);
            // В случае ошибки оставляем стандартный текст
            $('#startPremiumPayment').text('Попробовать');
        }
    },

    /**
     * Запуск бесплатного отчета
     */
    async startFreeReport() {
        try {
            console.log('🆓 Начинаем запуск бесплатного отчета...');
            
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            console.log('👤 Получен Telegram ID:', telegramId);
            
            // Тактильная обратная связь
            if (window.TelegramWebApp) {
                window.TelegramWebApp.hapticFeedback('light');
            }

            console.log('🆓 Запуск бесплатного отчета для пользователя:', telegramId);
            
            // Проверяем доступность ApiClient
            if (typeof ApiClient === 'undefined') {
                console.error('❌ ApiClient недоступен');
                if (window.TelegramWebApp) {
                    window.TelegramWebApp.showAlert('Ошибка: ApiClient недоступен');
                }
                return;
            }
            
            console.log('📡 Отправляем запрос к API...');
            
            // Проверяем, заполнил ли пользователь профиль
            const profile = await ApiClient.getUserProfile(telegramId);
            console.log('📊 Получен профиль:', profile);
            
            const user = profile && profile.user ? profile.user : null;
            const hasName = !!(user && user.name && String(user.name).trim());
            const hasAge = !!(user && typeof user.age === 'number' && user.age > 0);
            const hasGender = !!(user && user.gender);
            
            console.log('🔍 Проверка профиля:', { hasName, hasAge, hasGender });

            if (hasName && hasAge && hasGender) {
                // Профиль заполнен, идем к вопросам
                console.log('✅ Профиль заполнен, перенаправляем на вопросы');
                window.location.href = 'question.html?type=free';
            } else {
                // Профиль не заполнен, идем к логину
                console.log('⚠️ Профиль не заполнен, перенаправляем на логин');
                window.location.href = 'login.html';
            }
            
        } catch (error) {
            console.error('❌ Ошибка при запуске бесплатного отчета:', error);
            console.error('❌ Детали ошибки:', error.message, error.stack);
            if (window.TelegramWebApp) {
                window.TelegramWebApp.showAlert('Ошибка при запуске бесплатного отчета. Попробуйте еще раз.');
            }
        }
    },

    /**
     * Запуск премиум отчета
     */
    async startPremiumPayment() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            // Тактильная обратная связь
            if (window.TelegramWebApp) {
                window.TelegramWebApp.hapticFeedback('light');
            }

            console.log('💳 Проверяем статус пользователя для премиум отчета:', telegramId);
            
            // Сначала проверяем статус оплаты
            const profile = await ApiClient.getUserProfile(telegramId);
            console.log('👤 Профиль пользователя:', profile);
            
            if (profile && profile.payment_status === 'completed') {
                // Пользователь уже оплатил, проверяем профиль
                const user = profile && profile.user ? profile.user : null;
                const hasName = !!(user && user.name && String(user.name).trim());
                const hasAge = !!(user && typeof user.age === 'number' && user.age > 0);
                const hasGender = !!(user && user.gender);
                if (hasName && hasAge && hasGender) {
                    // Профиль заполнен, идем к вопросам
                    console.log('✅ Пользователь оплатил и профиль заполнен, перенаправляем на вопросы');
                    this.safeHapticFeedback('light');
                    window.location.href = 'question.html';
                } else {
                    // Профиль не заполнен, идем к логину
                    console.log('✅ Пользователь оплатил, но профиль не заполнен, идем к логину');
                    this.safeHapticFeedback('light');
                    window.location.href = 'login.html';
                }
            } else {
                // Пользователь не оплатил, создаем платежную ссылку
                console.log('💳 Создание платежной ссылки для пользователя:', telegramId);
                
                const response = await fetch(`${window.location.origin}/api/user/${telegramId}/start-premium-payment`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    console.log('✅ Платежная ссылка получена:', data.payment_link);
                    this.safeHapticFeedback('light');
                    // Перенаправляем пользователя на платежную страницу
                    window.location.href = data.payment_link;
                } else {
                    console.error('❌ Ошибка при получении платежной ссылки:', data);
                    this.safeShowAlert('Ошибка при создании платежа. Попробуйте позже.');
                }
            }
            
        } catch (error) {
            console.error('❌ Ошибка при запуске премиум отчета:', error);
            this.safeShowAlert('Ошибка при создании платежа. Попробуйте позже.');
        }
    },

    /**
     * Проверка статуса платежа при загрузке
     */
    async checkPaymentStatusOnLoad() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            // Проверяем, что ApiClient доступен
            if (typeof ApiClient === 'undefined') {
                console.warn('⚠️ ApiClient недоступен, пропускаем проверку статуса');
                return;
            }
            
            console.log('🔍 Проверяем статус платежа для пользователя:', telegramId);
            
            const status = await ApiClient.getUserProfile(telegramId);
            console.log('💳 Статус платежа:', status);
            
            if (status && status.payment_status === 'completed') {
                // Если оплата завершена, но профиль не заполнен — отправляем на login
                const user = status && status.user ? status.user : null;
                const hasName = !!(user && user.name && String(user.name).trim());
                const hasAge = !!(user && typeof user.age === 'number' && user.age > 0);
                const hasGender = !!(user && user.gender);

                if (!hasName || !hasAge || !hasGender) {
                    console.log('✅ Оплачено, но профиль не заполнен — редирект на login');
                    setTimeout(() => {
                        window.location.href = 'login.html';
                    }, 100);
                } else {
                    console.log('✅ Платеж завершен и профиль заполнен, перенаправляем на question');
                    setTimeout(() => {
                        window.location.href = 'question.html';
                    }, 100);
                }
                return;
            }
            
            if (status && status.payment_status === 'pending') {
                console.log('⏳ Платеж в процессе, перенаправляем на payment');
                setTimeout(() => {
                    window.location.href = 'payment.html';
                }, 100);
                return;
            }
            
            console.log('🆕 Нет активного платежа, остаемся на странице цен');
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса платежа:', error);
            console.log('🔄 Продолжаем загрузку страницы цен');
        }
    },

    /**
     * Безопасная тактильная обратная связь
     */
    safeHapticFeedback(type = 'light') {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hapticFeedback(type);
        }
    },

    /**
     * Безопасное отображение алерта
     */
    safeShowAlert(message) {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showAlert(message);
        } else {
            alert(message);
        }
    }
}; 