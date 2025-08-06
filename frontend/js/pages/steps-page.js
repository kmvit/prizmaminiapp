/**
 * Страница шагов (steps.html)
 * Инициализация и логика страницы шагов
 */

'use strict';

// Создаем глобальный объект для страницы шагов
window.StepsPage = {
    /**
     * Инициализация страницы шагов
     */
    init() {
        console.log('📋 Инициализация страницы шагов');
        
        this.setupTelegramUI();
    },

    /**
     * Настройка Telegram UI для страницы шагов
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showBackButton(() => {
                window.location.href = 'index.html';
            });
            window.TelegramWebApp.showMainButton('Продолжить', () => {
                window.location.href = 'price.html';
            });
        }
    }
}; 