/**
 * Страница платежа (payment.html)
 * Инициализация и логика страницы платежа
 */

'use strict';

window.PaymentPage = {
    /**
     * Инициализация страницы платежа
     */
    init() {
        console.log('💳 Инициализация страницы платежа');
        
        this.setupTelegramUI();
        this.startPaymentStatusMonitoring();
    },

    /**
     * Настройка Telegram UI для страницы платежа
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            try {
                if (window.TelegramWebApp.showBackButton) {
                    window.TelegramWebApp.showBackButton(() => {
                        window.location.href = 'price.html';
                    });
                }
                if (window.TelegramWebApp.hideMainButton) {
                    window.TelegramWebApp.hideMainButton();
                }
            } catch (error) {
                console.log('⚠️ Ошибка настройки кнопок Telegram:', error);
            }
        }
    },

    /**
     * Запуск мониторинга статуса платежа
     */
    startPaymentStatusMonitoring() {
        console.log('🔍 Запуск мониторинга статуса платежа');
        
        // Проверяем статус каждые 3 секунды
        const checkInterval = setInterval(async () => {
            try {
                const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
                
                const status = await ApiClient.getUserProfile(telegramId);
                console.log('💳 Статус платежа:', status);
                
                if (status.payment_status === 'completed') {
                    console.log('✅ Платеж завершен, перенаправляем на complete-payment');
                    clearInterval(checkInterval);
                    window.location.href = 'complete-payment.html';
                    return;
                }
                
                if (status.payment_status === 'failed') {
                    console.log('❌ Платеж не удался, перенаправляем на uncomplete-payment');
                    clearInterval(checkInterval);
                    window.location.href = 'uncomplete-payment.html';
                    return;
                }
                
                // Платеж все еще в процессе
                console.log('⏳ Платеж в процессе...');
                
            } catch (error) {
                console.error('❌ Ошибка при проверке статуса платежа:', error);
            }
        }, 3000);
        
        // Останавливаем мониторинг через 5 минут
        setTimeout(() => {
            clearInterval(checkInterval);
            console.log('⏰ Таймаут мониторинга платежа');
        }, 300000); // 5 минут
    }
}; 