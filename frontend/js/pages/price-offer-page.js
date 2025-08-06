/**
 * Страница спецпредложения (price-offer.html)
 * Инициализация и логика страницы спецпредложения
 */

'use strict';

window.PriceOfferPage = {
    /**
     * Инициализация страницы спецпредложения
     */
    init() {
        console.log('🎁 Инициализация страницы спецпредложения');
        
        this.setupTelegramUI();
        this.checkPaymentStatusOnLoad();
        this.setupEventHandlers();
    },

    /**
     * Настройка Telegram UI для страницы спецпредложения
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showBackButton(() => {
                window.location.href = 'price.html';
            });
            window.TelegramWebApp.hideMainButton();
        }
    },

    /**
     * Проверка статуса платежа при загрузке
     */
    async checkPaymentStatusOnLoad() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            const status = await ApiClient.getUserProfile(telegramId);
            console.log('💳 Статус платежа:', status);
            
            if (status.payment_status === 'completed') {
                console.log('✅ Платеж завершен, перенаправляем на question');
                window.location.href = 'question.html';
                return;
            }
            
            if (status.payment_status === 'pending') {
                console.log('⏳ Платеж в процессе, перенаправляем на payment');
                window.location.href = 'payment.html';
                return;
            }
            
            console.log('🆕 Нет активного платежа, остаемся на странице спецпредложения');
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса платежа:', error);
        }
    },

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        console.log('🔧 Настройка обработчиков событий');
        console.log('🔧 Кнопка downloadFreeReport найдена:', $('#downloadFreeReport').length);
        
        // Обработка кнопки скачивания бесплатного отчета
        $('#downloadFreeReport').off('click').on('click', async (e) => {
            console.log('📥 Нажата кнопка скачивания бесплатного отчета');
            e.preventDefault();
            this.safeHapticFeedback('medium');
            
            const telegramId = this.getTelegramUserId();
            if (!telegramId) {
                this.safeShowAlert('Ошибка: не удалось получить ID пользователя');
                return;
            }
            
            const $button = $(e.currentTarget);
            const $span = $button.find('.download-file-text span');
            const originalText = $span.text();
            
            try {
                // Показываем индикатор загрузки
                $button.addClass('loading');
                $span.text('Скачиваем отчет...');
                
                // Проверяем статус отчетов для получения URL бесплатного отчета
                const reportsResponse = await fetch(`${window.location.origin}/api/user/${telegramId}/reports-status`);
                const reportsData = await reportsResponse.json();
                
                if (reportsResponse.ok && reportsData.available_report && reportsData.available_report.status === 'ready') {
                    const availableReport = reportsData.available_report;
                    
                    // Убеждаемся, что это бесплатный отчет
                    if (availableReport.type === 'free') {
                        const reportUrl = `${window.location.origin}${availableReport.download_url}?download=1&source=telegram&t=${Date.now()}`;
                        
                        // Используем Telegram API для скачивания
                        if (window.TelegramWebApp && window.TelegramWebApp.isInTelegram()) {
                            window.TelegramWebApp.openLink(reportUrl);
                            $span.text('Отчет открыт!');
                            this.safeHapticFeedback('light');
                            
                            if (window.TelegramWebApp.showAlert) {
                                window.TelegramWebApp.showAlert('📁 Бесплатный отчет открыт в браузере!\n\n' +
                                    '💡 Браузер должен автоматически скачать файл.\n' +
                                    'Если этого не произошло - проверьте папку "Загрузки".\n\n' +
                                    '📄 Имя файла: prizma-report-' + telegramId + '.pdf');
                            }
                        } else {
                            window.open(reportUrl, '_blank');
                            $span.text('Отчет открыт!');
                        }
                    } else {
                        this.safeShowAlert('Ошибка: доступен только премиум отчет');
                        $span.text(originalText);
                    }
                } else {
                    this.safeShowAlert('Отчет не готов. Попробуйте позже.');
                    $span.text(originalText);
                }
            } catch (error) {
                console.error('❌ Ошибка при скачивании бесплатного отчета:', error);
                this.safeShowAlert('Ошибка при скачивании отчета. Попробуйте позже.');
                $span.text(originalText);
            } finally {
                $button.removeClass('loading');
            }
        });

        // Обработка кнопки "Выбрать способ оплаты" для премиум отчета
        $('#startPremiumFromOffer').off('click').on('click', async (e) => {
            e.preventDefault();
            this.safeHapticFeedback('medium');

            const $button = $(e.currentTarget);
            const originalText = $button.html();
            const telegramId = this.getTelegramUserId();

            try {
                $button.prop('disabled', true).html('Загрузка...');

                const response = await fetch(`${window.location.origin}/api/user/${telegramId}/start-premium-payment`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    console.log('✅ Платежная ссылка получена:', data.payment_link);
                    this.safeHapticFeedback('light');
                    // Перенаправляем пользователя на платежную страницу
                    window.location.href = data.payment_link;
                } else {
                    console.error('❌ Ошибка при получении платежной ссылки:', data);
                    this.safeShowAlert('Ошибка при создании платежа. Попробуйте позже.');
                    $button.prop('disabled', false).html(originalText);
                }
            } catch (error) {
                console.error('❌ Ошибка при создании платежа:', error);
                this.safeShowAlert('Ошибка при создании платежа. Попробуйте позже.');
                $button.prop('disabled', false).html(originalText);
            }
        });
    },

    /**
     * Получение Telegram ID пользователя
     */
    getTelegramUserId() {
        return window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
    },

    /**
     * Безопасная тактильная обратная связь
     */
    safeHapticFeedback(type = 'light') {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hapticFeedback(type);
        }
    },

    /**
     * Безопасное отображение алерта
     */
    safeShowAlert(message) {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showAlert(message);
        } else {
            alert(message);
        }
    }
}; 