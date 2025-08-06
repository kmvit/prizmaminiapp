/**
 * Страница входа (login.html)
 * Инициализация и логика страницы входа
 */

'use strict';

// Создаем глобальный объект для страницы входа
window.LoginPage = {
    /**
     * Инициализация страницы входа
     */
    init() {
        console.log('👤 Инициализация страницы входа');
        
        this.setupTelegramUI();
        this.setupUI();
        this.checkUserStatus();
    },

    /**
     * Настройка Telegram UI для страницы входа
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
     * Настройка UI элементов
     */
    setupUI() {
        UIHelpers.setupSelectDropdown();
    },

    /**
     * Проверка статуса пользователя
     */
    async checkUserStatus() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            const progress = await ApiClient.getUserProgress(telegramId);
            
            console.log('👤 Статус пользователя:', progress);
            
            if (progress.completed_questions >= 15) {
                console.log('✅ Все вопросы завершены, перенаправляем на loading');
                window.location.href = 'loading.html';
                return;
            }
            
            if (progress.completed_questions > 0) {
                console.log('📝 Есть незавершенные вопросы, перенаправляем на question');
                window.location.href = 'question.html';
                return;
            }
            
            console.log('🆕 Новый пользователь, остаемся на странице входа');
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса пользователя:', error);
        }
    }
}; 