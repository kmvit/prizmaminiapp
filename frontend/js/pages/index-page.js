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

            // Быстрый путь: если уже знаем, что отчет готов, не дергаем API повторно
            try {
                const cached = localStorage.getItem('prizma_report_ready');
                if (cached) {
                    const data = JSON.parse(cached);
                    if (data && data.type === 'premium') {
                        console.log('📝 Кэш: премиум отчет готов — сразу на download');
                        window.location.href = 'download.html';
                        return;
                    } else if (data && data.type === 'free') {
                        console.log('📝 Кэш: бесплатный отчет готов — сразу на price-offer');
                        window.location.href = 'price-offer.html';
                        return;
                    }
                }
            } catch (_) {}
            
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
                console.log('⏳ Отчет генерируется — показываем сообщение и закрываем приложение');
                try { window.TelegramWebApp?.showAlert('Ваш отчет уже генерируется. Зайдите позже или мы пришлем его вам в боте, как только он будет готов.'); } catch (_) {}
                try { window.TelegramWebApp?.close(); } catch (_) { try { window.close(); } catch (e) {} }
                return;
            }
            
            // Проверяем премиум отчет в процессе генерации
            if (reportsStatus.premium_report && reportsStatus.premium_report.status === 'processing') {
                console.log('⏳ Премиум отчет генерируется — показываем сообщение и закрываем приложение');
                try { window.TelegramWebApp?.showAlert('Ваш премиум-отчет уже генерируется. Зайдите позже или мы пришлем его вам в боте, как только он будет готов.'); } catch (_) {}
                try { window.TelegramWebApp?.close(); } catch (_) { try { window.close(); } catch (e) {} }
                return;
            }
            
            // Проверяем, есть ли готовый отчет
            if (reportsStatus.available_report && reportsStatus.available_report.status === 'ready') {
                if (reportsStatus.available_report.type === 'premium') {
                    console.log('✅ Премиум отчет готов, перенаправляем на download');
                    window.location.href = 'download.html';
                } else {
                    console.log('🆓 Бесплатный отчет готов, перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                }
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