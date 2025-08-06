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
        
        this.setupTelegramUI();
        this.setupEventHandlers();
        this.checkPaymentStatusOnLoad();
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
     * Запуск бесплатного отчета
     */
    async startFreeReport() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            // Тактильная обратная связь
            if (window.TelegramWebApp) {
                window.TelegramWebApp.hapticFeedback('light');
            }

            console.log('🔄 Создание бесплатного отчета для пользователя:', telegramId);
            
            // Перенаправляем на страницу вопросов для бесплатного отчета
            window.location.href = 'question.html?type=free';
            
        } catch (error) {
            console.error('❌ Ошибка при запуске бесплатного отчета:', error);
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

            console.log('💳 Запуск процесса оплаты для пользователя:', telegramId);
            
            // Создаем платежную ссылку напрямую
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
            
            const status = await ApiClient.getUserProfile(telegramId);
            console.log('💳 Статус платежа:', status);
            
            if (status.payment_status === 'completed') {
                console.log('✅ Платеж завершен, перенаправляем на question');
                window.location.href = 'question.html';
                return;
            }
            
            if (status.payment_status === 'pending') {
                console.log('⏳ Платеж в процессе, перенаправляем на payment');
                window.location.href = 'payment.html';
                return;
            }
            
            console.log('🆕 Нет активного платежа, остаемся на странице цен');
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса платежа:', error);
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