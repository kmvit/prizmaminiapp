/**
 * Страница загрузки (loading.html)
 * Инициализация и логика страницы загрузки
 */

'use strict';

// Создаем глобальный объект для страницы загрузки
window.LoadingPage = {
    /**
     * Инициализация страницы загрузки
     */
    init() {
        console.log('⏳ Инициализация страницы загрузки');
        
        this.setupTelegramUI();
        this.startReportGeneration();
    },

    /**
     * Настройка Telegram UI для страницы загрузки
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hideBackButton();
            window.TelegramWebApp.hideMainButton();
        }
    },

    /**
     * Запуск генерации отчета
     */
    async startReportGeneration() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            console.log('🚀 Запуск генерации отчета для пользователя:', telegramId);
            
            // Запускаем генерацию отчета
            await ApiClient.generateReport(telegramId);
            
            // Начинаем мониторинг статуса
            this.checkReportStatus();
            
        } catch (error) {
            console.error('❌ Ошибка при запуске генерации отчета:', error);
            window.TelegramWebApp?.showAlert('Ошибка при генерации отчета');
        }
    },

    /**
     * Проверка статуса отчета
     */
    async checkReportStatus() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            const status = await ApiClient.getReportsStatus(telegramId);
            console.log('📊 Статус отчета:', status);
            console.log('📊 available_report:', status.available_report);
            console.log('📊 free_report:', status.free_report);
            console.log('📊 premium_report:', status.premium_report);
            
            // Если тест не завершен, перенаправляем на страницу с вопросами
            if (status.status === 'test_not_completed') {
                console.log('❌ Тест не завершен, перенаправляем на страницу с вопросами');
                console.log('📊 Сообщение:', status.message);
                window.location.href = 'question.html';
                return;
            }
            
            // Проверяем доступный отчет
            if (status.available_report && status.available_report.status === 'ready') {
                console.log('✅ Отчет готов, перенаправляем на download');
                window.location.href = 'download.html';
                return;
            }
            
            // Проверяем, генерируется ли отчет
            if (status.available_report && status.available_report.status === 'processing') {
                console.log('⏳ Отчет генерируется, проверяем через 3 секунды');
                setTimeout(() => {
                    this.checkReportStatus();
                }, 3000);
                return;
            }
            
            // Если нет доступного отчета, но есть бесплатный отчет в процессе
            if (status.free_report && status.free_report.status === 'processing') {
                console.log('⏳ Бесплатный отчет генерируется, проверяем через 3 секунды');
                setTimeout(() => {
                    this.checkReportStatus();
                }, 3000);
                return;
            }
            
            console.log('❌ Неожиданный статус отчета:', status);
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса отчета:', error);
            // Повторяем проверку через 5 секунд
            setTimeout(() => {
                this.checkReportStatus();
            }, 5000);
        }
    }
}; 