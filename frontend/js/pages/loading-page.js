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
            
            // Сначала проверяем статус пользователя и отчетов
            const status = await ApiClient.getReportsStatus(telegramId);
            console.log('📊 Статус пользователя:', status);
            console.log('📊 free_report_status:', status.free_report_status);
            console.log('📊 premium_report_status:', status.premium_report_status);
            console.log('📊 available_report:', status.available_report);
            
            // Если тест не завершен, перенаправляем на страницу с вопросами
            if (status.status === 'test_not_completed') {
                console.log('❌ Тест не завершен, перенаправляем на страницу с вопросами');
                window.location.href = 'question.html';
                return;
            }
            
            // Если тест завершен, но отчет еще не генерировался - запускаем генерацию
            if (status.free_report_status && status.free_report_status.status === 'not_ready') {
                console.log('🆓 Тест завершен, но отчет не готов. Запускаем генерацию бесплатного отчета.');
                const result = await ApiClient.generateReport(telegramId);
                console.log('📊 Результат генерации бесплатного отчета:', result);
                
                // Проверяем, не оплатил ли пользователь премиум
                if (result.status === 'premium_paid') {
                    console.log('💎 Пользователь оплатил премиум, запускаем премиум генерацию');
                    await ApiClient.generatePremiumReport(telegramId);
                }
                
                // Начинаем мониторинг статуса
                setTimeout(() => {
                    this.checkReportStatus();
                }, 5000);
                return;
            }
            
            // Проверяем, есть ли уже готовый отчет
            if (status.available_report && status.available_report.status === 'ready') {
                console.log('✅ Отчет уже готов, проверяем тип пользователя');
                
                // Проверяем тип отчета
                if (status.available_report.type === 'premium') {
                    console.log('💎 Премиум отчет готов, перенаправляем на download');
                    try { localStorage.setItem('prizma_report_ready', JSON.stringify({ type: 'premium', t: Date.now() })); } catch(_) {}
                    window.location.href = 'download.html';
                } else if (status.available_report.type === 'free') {
                    console.log('🆓 Бесплатный отчет готов, перенаправляем на price-offer');
                    try { localStorage.setItem('prizma_report_ready', JSON.stringify({ type: 'free', t: Date.now() })); } catch(_) {}
                    window.location.href = 'price-offer.html';
                } else {
                    console.log('❓ Неизвестный тип отчета, перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                }
                return;
            }
            
            // Определяем какой отчет нужно генерировать
            const user = status;
            // В ответе есть флаги is_paid в корневом объекте и внутри available_report
            console.log('💰 Статус оплаты пользователя:', { is_paid: status.is_paid, available_report: status.available_report });
            
            // Проверяем, есть ли уже готовый отчет
            if (status.free_report_status && status.free_report_status.status === 'ready') {
                console.log('✅ Бесплатный отчет уже готов, перенаправляем на price-offer');
                try { localStorage.setItem('prizma_report_ready', JSON.stringify({ type: 'free', t: Date.now() })); } catch(_) {}
                window.location.href = 'price-offer.html';
                return;
            }
            
            // Проверяем, завершен ли премиум тест для оплативших пользователей
            if (status.is_paid) {
                // Проверяем, есть ли еще вопросы для премиум пользователя
                const progress = await ApiClient.getUserProgress(telegramId);
                console.log('📊 Прогресс премиум пользователя:', progress);
                
                if (progress.progress && progress.progress.answered < progress.progress.total) {
                    console.log('🔄 Премиум пользователь еще не завершил все вопросы, перенаправляем на вопросы');
                    window.location.href = 'question.html';
                    return;
                }
                
                // Если все вопросы пройдены, запускаем генерацию премиум отчета
                console.log('💎 Премиум пользователь завершил все вопросы, запускаем генерацию премиум отчета');
                const startResp = await ApiClient.generatePremiumReport(telegramId);
                if (startResp && (startResp.status === 'already_processing' || startResp.status === 'processing')) {
                    const msg = 'Ваш премиум-отчет уже генерируется. Мы пришлем его вам в боте, как только он будет готов.';
                    console.log('ℹ️ ' + msg);
                    try { window.TelegramWebApp?.showAlert(msg); } catch (_) {}
                    // Если пришла ссылка на бота - открываем
                    if (startResp.bot_link) {
                        try { window.TelegramWebApp?.openTelegramLink(startResp.bot_link); } catch (_) {}
                    }
                    // Завершаем дальнейшую генерацию/проверки и выходим
                    return;
                }
            } else {
                // Пользователь не оплатил - запускаем генерацию бесплатного отчета
                console.log('🆓 Запускаем генерацию бесплатного отчета');
                const result = await ApiClient.generateReport(telegramId);
                console.log('📊 Результат генерации бесплатного отчета:', result);
                
                // Проверяем, не оплатил ли пользователь премиум
                if (result.status === 'premium_paid') {
                    console.log('💎 Пользователь оплатил премиум, запускаем премиум генерацию');
                    await ApiClient.generatePremiumReport(telegramId);
                }
            }
            
            // Начинаем мониторинг статуса с интервалом 30 секунд
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
                console.log('✅ Отчет готов, проверяем тип пользователя');
                
                // Проверяем тип отчета
                if (status.available_report.type === 'premium') {
                    // Дополнительно проверяем, что премиум действительно READY и есть путь к PDF
                    if (status.premium_report && status.premium_report.status === 'ready' && status.premium_report.report_path && status.premium_report.report_path.endsWith('.pdf')) {
                        console.log('💎 Премиум отчет готов, перенаправляем на download');
                        try { localStorage.setItem('prizma_report_ready', JSON.stringify({ type: 'premium', t: Date.now() })); } catch(_) {}
                        window.location.href = 'download.html';
                        return;
                    } else {
                        console.log('⏳ Премиум еще не готов (или нет PDF), остаемся на загрузке');
                        setTimeout(() => { this.checkReportStatus(); }, 15000);
                        return;
                    }
                } else if (status.available_report.type === 'free') {
                    console.log('🆓 Бесплатный отчет готов, перенаправляем на price-offer');
                    try { localStorage.setItem('prizma_report_ready', JSON.stringify({ type: 'free', t: Date.now() })); } catch(_) {}
                    window.location.href = 'price-offer.html';
                    return;
                } else {
                    console.log('❓ Неизвестный тип отчета, перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                    return;
                }
            }
            
            // Проверяем, генерируется ли премиум-отчет
            if (status.premium_report_status && status.premium_report_status.status === 'processing') {
                console.log('⏳ Премиум отчет генерируется — информируем пользователя и закрываем приложение');
                try { window.TelegramWebApp?.showAlert('Ваш премиум-отчет уже генерируется. Мы пришлем его вам в боте, как только он будет готов.'); } catch (_) {}
                try { window.TelegramWebApp?.close(); } catch (_) { try { window.close(); } catch (e) {} }
                return;
            }
            
            // Проверяем статус premium_paid от бесплатного отчета
            if (status.free_report_status && status.free_report_status.status === 'premium_paid') {
                console.log('💎 Пользователь оплатил премиум, запускаем премиум генерацию');
                ApiClient.generatePremiumReport(telegramId).then(() => {
                    // Начинаем мониторинг статуса
                    setTimeout(() => {
                        this.checkReportStatus();
                    }, 30000);
                }).catch(error => {
                    console.error('❌ Ошибка при запуске премиум генерации:', error);
                });
                return;
            }
            
            // Проверяем статус payment_required от премиум отчета
            if (status.premium_report_status && status.premium_report_status.status === 'payment_required') {
                console.log('💰 Требуется оплата для премиум отчета, перенаправляем на оплату');
                window.location.href = 'price.html';
                return;
            }
            
            // Если нет доступного отчета, но есть бесплатный отчет в процессе
            if (status.free_report_status && status.free_report_status.status === 'processing') {
                console.log('⏳ Бесплатный отчет генерируется — информируем пользователя и закрываем приложение');
                try { window.TelegramWebApp?.showAlert('Ваш отчет уже генерируется. Мы пришлем его вам в боте, как только он будет готов.'); } catch (_) {}
                try { window.TelegramWebApp?.close(); } catch (_) { try { window.close(); } catch (e) {} }
                return;
            }
            
            // Если нет доступного отчета
            if (status.available_report && status.available_report.status === 'not_available') {
                console.log('❌ Нет доступного отчета, перенаправляем на страницу с вопросами');
                window.location.href = 'question.html';
                return;
            }
            
            // Если отчет не удалось сгенерировать
            if (status.available_report && status.available_report.status === 'failed') {
                console.log('❌ Ошибка генерации отчета:', status.available_report.message);
                window.TelegramWebApp?.showAlert('Ошибка генерации отчета. Попробуйте позже.');
                setTimeout(() => {
                    window.location.href = 'question.html';
                }, 3000);
                return;
            }
            
            // Если требуется оплата
            if (status.available_report && status.available_report.status === 'payment_required') {
                console.log('💰 Требуется оплата, перенаправляем на страницу оплаты');
                window.location.href = 'price.html';
                return;
            }
            
            // Если премиум отчет еще не сгенерирован
            if (status.available_report && status.available_report.status === 'not_started' && status.available_report.type === 'premium') {
                console.log('💎 Премиум отчет еще не сгенерирован, запускаем генерацию');
                ApiClient.generatePremiumReport(telegramId).then(() => {
                    // Начинаем мониторинг статуса
                    setTimeout(() => {
                        this.checkReportStatus();
                    }, 30000);
                }).catch(error => {
                    console.error('❌ Ошибка при запуске премиум генерации:', error);
                });
                return;
            }
            
            console.log('❌ Неожиданный статус отчета:', status);
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса отчета:', error);
            // Повторяем проверку через 30 секунд
            setTimeout(() => {
                this.checkReportStatus();
            }, 30000);
        }
    }
}; 