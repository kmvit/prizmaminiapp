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
            
            // Сначала проверяем статус отчетов
            const reportsStatus = await ApiClient.getReportsStatus(telegramId);
            console.log('📊 Статус отчетов:', reportsStatus);
            
            // Если тест не завершен, проверяем прогресс
            if (reportsStatus.status === 'test_not_completed') {
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
                return;
            }
            
            // Проверяем, генерируется ли отчет
            if (reportsStatus.available_report && reportsStatus.available_report.status === 'processing') {
                console.log('⏳ Отчет генерируется, перенаправляем на loading');
                window.location.href = 'loading.html';
                return;
            }
            
            // Проверяем премиум отчет в процессе генерации
            if (reportsStatus.premium_report && reportsStatus.premium_report.status === 'processing') {
                console.log('⏳ Премиум отчет генерируется, перенаправляем на loading');
                window.location.href = 'loading.html';
                return;
            }
            
            // Проверяем, есть ли готовый отчет
            if (reportsStatus.available_report && reportsStatus.available_report.status === 'ready') {
                console.log('✅ Отчет готов, перенаправляем на download');
                window.location.href = 'download.html';
                return;
            }
            
            // Если есть бесплатный отчет в процессе
            if (reportsStatus.free_report && reportsStatus.free_report.status === 'processing') {
                console.log('⏳ Бесплатный отчет генерируется, перенаправляем на loading');
                window.location.href = 'loading.html';
                return;
            }
            
            // Если тест завершен, но отчет еще не начал генерироваться
            if (reportsStatus.status === 'test_completed') {
                console.log('✅ Тест завершен, перенаправляем на loading для запуска генерации');
                window.location.href = 'loading.html';
                return;
            }
            
            console.log('🆕 Новый пользователь, остаемся на главной странице');
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса пользователя:', error);
        }
    }
}; 