/**
 * Страница неуспешного платежа (uncomplete-payment.html)
 * Инициализация и логика страницы неуспешного платежа
 */

'use strict';

window.uncomplete-paymentPage = {
    /**
     * Инициализация страницы неуспешного платежа
     */
    init() {
        console.log('❌ Инициализация страницы неуспешного платежа');
        
        this.setupTelegramUI();
    },

    /**
     * Настройка Telegram UI для страницы неуспешного платежа
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hideBackButton();
            window.TelegramWebApp.showMainButton('Попробовать снова', () => {
                window.location.href = 'price.html';
            });
        }
    }
}; 