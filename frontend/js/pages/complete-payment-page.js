/**
 * Страница успешного платежа (complete-payment.html)
 * Инициализация и логика страницы успешного платежа
 */

'use strict';

window.CompletePaymentPage = {
    /**
     * Инициализация страницы успешного платежа
     */
    init() {
        console.log('✅ Инициализация страницы успешного платежа');
        
        this.setupTelegramUI();
        this.determineCorrectQuestion();
    },

    /**
     * Настройка Telegram UI для страницы успешного платежа
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            try {
                if (window.TelegramWebApp.hideBackButton) {
                    window.TelegramWebApp.hideBackButton();
                }
                if (window.TelegramWebApp.showMainButton) {
                    window.TelegramWebApp.showMainButton('Продолжить', () => {
                        window.location.href = 'question.html';
                    });
                }
            } catch (error) {
                console.log('⚠️ Ошибка настройки кнопок Telegram:', error);
            }
        }
    },

    /**
     * Определение правильного вопроса для продолжения
     */
    async determineCorrectQuestion() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            const progress = await ApiClient.getUserProgress(telegramId);
            console.log('📊 Прогресс пользователя:', progress);
            
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
            
            console.log('🆕 Новый пользователь после платежа, перенаправляем на question');
            window.location.href = 'question.html';
            
        } catch (error) {
            console.error('❌ Ошибка при определении правильного вопроса:', error);
            // В случае ошибки перенаправляем на главную страницу
            window.location.href = 'index.html';
        }
    }
}; 