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
            
            // Если тест не завершен, перенаправляем на страницу с вопросами
            if (status.status === 'test_not_completed') {
                console.log('❌ Тест не завершен, перенаправляем на страницу с вопросами');
                window.location.href = 'question.html';
                return;
            }
            
            // Проверяем, есть ли уже готовый отчет
            if (status.available_report && status.available_report.status === 'ready') {
                console.log('✅ Отчет уже готов, проверяем тип пользователя');
                
                // Проверяем тип отчета
                if (status.available_report.type === 'premium') {
                    console.log('💎 Премиум отчет готов, перенаправляем на download');
                    window.location.href = 'download.html';
                } else if (status.available_report.type === 'free') {
                    console.log('🆓 Бесплатный отчет готов, перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                } else {
                    console.log('❓ Неизвестный тип отчета, перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                }
                return;
            }
            
            // Определяем какой отчет нужно генерировать
            const user = status.user;
            console.log('💰 Статус оплаты пользователя:', user);
            
            if (user && user.is_paid) {
                // Пользователь оплатил премиум - запускаем генерацию премиум отчета
                console.log('💎 Запускаем генерацию премиум отчета');
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
                    console.log('💎 Премиум отчет готов, перенаправляем на download');
                    window.location.href = 'download.html';
                    return;
                } else if (status.available_report.type === 'free') {
                    console.log('🆓 Бесплатный отчет готов, перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                    return;
                } else {
                    console.log('❓ Неизвестный тип отчета, перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                    return;
                }
            }
            
            // Проверяем, генерируется ли премиум-отчет
            if (status.premium_report && status.premium_report.status === 'processing') {
                console.log('⏳ Отчет генерируется, проверяем через 30 секунд');
                setTimeout(() => {
                    this.checkReportStatus();
                }, 30000);
                return;
            }
            
            // Проверяем статус premium_paid от бесплатного отчета
            if (status.free_report && status.free_report.status === 'premium_paid') {
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
            if (status.premium_report && status.premium_report.status === 'payment_required') {
                console.log('💰 Требуется оплата для премиум отчета, перенаправляем на оплату');
                window.location.href = 'price.html';
                return;
            }
            
            // Если нет доступного отчета, но есть бесплатный отчет в процессе
            if (status.free_report && status.free_report.status === 'processing') {
                console.log('⏳ Бесплатный отчет генерируется, проверяем через 30 секунд');
                setTimeout(() => {
                    this.checkReportStatus();
                }, 30000);
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