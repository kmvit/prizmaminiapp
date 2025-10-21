/**
 * Страница неуспешного платежа (uncomplete-payment.html)
 * Инициализация и логика страницы неуспешного платежа
 */

'use strict';

window.UncompletePaymentPage = {
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
            try {
                if (window.TelegramWebApp.hideBackButton) {
                    window.TelegramWebApp.hideBackButton();
                }
                if (window.TelegramWebApp.showMainButton) {
                    window.TelegramWebApp.showMainButton('Попробовать снова', () => {
                        // Возвращаемся на страницу спецпредложения, чтобы сохранить акцию
                        window.location.href = 'price-offer.html';
                    });
                }
            } catch (error) {
                console.log('⚠️ Ошибка настройки кнопок Telegram:', error);
            }
        }
    }
}; 