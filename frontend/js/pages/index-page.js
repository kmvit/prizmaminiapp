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
            // Убрано использование localStorage — всегда проверяем статус через API
            
            // Сначала проверяем статус отчетов
            const reportsStatus = await ApiClient.getReportsStatus(telegramId);
            console.log('📊 Статус отчетов:', reportsStatus);
            
            // Если тест не завершен, проверяем прогресс
            if (reportsStatus.status === 'test_not_completed') {
                const progress = await ApiClient.getUserProgress(telegramId);
                console.log('👤 Прогресс пользователя:', progress);

                const answered = progress?.progress?.answered ?? 0;
                const total = progress?.progress?.total ?? 0;

                if (total > 0 && answered >= total) {
                    console.log('✅ Все вопросы завершены, перенаправляем на loading');
                    window.location.href = 'loading.html';
                    return;
                }
                if (answered > 0) {
                    console.log('📝 Есть незавершенные вопросы, перенаправляем на question');
                    window.location.href = 'question.html';
                    return;
                }

                console.log('🆕 Новый пользователь, остаемся на главной странице');
                return;
            }
            
            // Проверяем, генерируется ли отчет (free или premium)
            const freeStatus = reportsStatus.free_report_status;
            const premiumStatus = reportsStatus.premium_report_status;
            if ((premiumStatus && premiumStatus.status === 'processing') || (freeStatus && freeStatus.status === 'processing') || (reportsStatus.available_report && reportsStatus.available_report.status === 'processing')) {
                console.log('⏳ Отчет генерируется — перенаправляем на loading, показываем сообщение и закрываем приложение');
                window.location.href = 'loading.html';
                setTimeout(() => {
                    try { window.TelegramWebApp?.showAlert('Ваш отчет генерируется. Мы пришлем его вам в боте, как только он будет готов.'); } catch (_) {}
                    try { window.TelegramWebApp?.close(); } catch (_) { try { window.close(); } catch (e) {} }
                }, 300);
                return;
            }
            
            // Проверяем премиум отчет в процессе генерации (доп. страховка)
            if (premiumStatus && premiumStatus.status === 'processing') {
                console.log('⏳ Премиум отчет генерируется — перенаправляем на loading и закрываем приложение');
                window.location.href = 'loading.html';
                setTimeout(() => {
                    try { window.TelegramWebApp?.showAlert('Ваш премиум-отчет уже генерируется. Мы пришлем его вам в боте, как только он будет готов.'); } catch (_) {}
                    try { window.TelegramWebApp?.close(); } catch (_) { try { window.close(); } catch (e) {} }
                }, 300);
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
            if (freeStatus && freeStatus.status === 'processing') {
                console.log('⏳ Бесплатный отчет генерируется, перенаправляем на loading');
                window.location.href = 'loading.html';
                return;
            }
            
            // Если тест завершен (общий успех) и нет готового отчета — переходим на loading
            if (reportsStatus.status === 'success' && (!reportsStatus.available_report || reportsStatus.available_report.status !== 'ready')) {
                console.log('✅ Тест завершен, перенаправляем на loading для запуска/ожидания генерации');
                window.location.href = 'loading.html';
                return;
            }
            
            console.log('🆕 Новый пользователь, остаемся на главной странице');
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса пользователя:', error);
        }
    }
}; 