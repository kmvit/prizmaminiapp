/**
 * Главная страница (index.html)
 * Инициализация и логика главной страницы
 */

'use strict';

// Создаем глобальный объект для главной страницы
window.IndexPage = {
    /**
     * Инициализация главной страницы
     */
    init() {
        console.log('🏠 Инициализация главной страницы');
        
        this.setupTelegramUI();
        this.checkUserStatus();
    },

    /**
     * Настройка Telegram UI для главной страницы
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showMainButton('Расшифровать меня', () => {
                window.location.href = 'steps.html';
            });
        }
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
            
            console.log('🆕 Новый пользователь, остаемся на главной странице');
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса пользователя:', error);
        }
    }
}; 