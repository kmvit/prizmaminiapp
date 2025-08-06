/**
 * Страница ответов (answers.html)
 * Инициализация и логика страницы ответов
 */

'use strict';

window.AnswersPage = {
    /**
     * Инициализация страницы ответов
     */
    init() {
        console.log('📝 Инициализация страницы ответов');
        
        this.setupTelegramUI();
    },

    /**
     * Настройка Telegram UI для страницы ответов
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hideBackButton();
            window.TelegramWebApp.hideMainButton();
        }
    }
}; 