/**
 * Страница скачивания (download.html)
 * Инициализация и логика страницы скачивания
 */

'use strict';

window.DownloadPage = {
    /**
     * Инициализация страницы скачивания
     */
    init() {
        console.log('📥 Инициализация страницы скачивания');
        
        this.setupTelegramUI();
        this.setupDownloadHandlers();
        this.checkUserStatusOnLoad();
    },

    /**
     * Настройка Telegram UI для страницы скачивания
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            try {
                if (window.TelegramWebApp.hideBackButton) {
                    window.TelegramWebApp.hideBackButton();
                }
                if (window.TelegramWebApp.hideMainButton) {
                    window.TelegramWebApp.hideMainButton();
                }
            } catch (error) {
                console.log('⚠️ Ошибка скрытия кнопок Telegram:', error);
            }
        }
    },

    /**
     * Настройка обработчиков скачивания
     */
    setupDownloadHandlers() {
        // Обработчик скачивания бесплатного отчета
        $('#download-free-report').on('click', () => {
            this.downloadReport('free');
        });

        // Обработчик скачивания премиум отчета
        $('#download-premium-report').on('click', () => {
            this.downloadReport('premium');
        });

        // Обработчик покупки премиум отчета
        $('#buy-premium-report').on('click', () => {
            this.startPremiumPayment();
        });

        // Обработчик основной кнопки скачивания
        $('#downloadReport').on('click', () => {
            console.log('📥 Нажата кнопка скачивания отчета');
            // Определяем тип отчета на основе статуса пользователя
            this.downloadReport('premium'); // На странице download.html всегда премиум отчет
        });
    },

    /**
     * Скачивание отчета
     */
    async downloadReport(reportType) {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            console.log(`📥 Скачивание отчета типа: ${reportType} для пользователя ${telegramId}`);
            console.log('🔧 DownloadUtils доступен:', !!window.DownloadUtils);
            console.log('🔧 UIHelpers доступен:', !!window.UIHelpers);
            
            // Показываем индикатор загрузки
            if (window.UIHelpers && window.UIHelpers.showLoadingIndicator) {
                UIHelpers.showLoadingIndicator();
            }
            
            // Для премиум отчетов используем специальную логику
            if (reportType === 'premium') {
                console.log('💎 Скачивание премиум отчета - принудительное скачивание');
                
                // Показываем специальное сообщение для премиум отчета
                if (window.TelegramWebApp) {
                    window.TelegramWebApp.showAlert(
                        '💎 Скачивание премиум отчета\n\n' +
                        '📱 Файл будет автоматически скачан на ваше устройство.\n' +
                        '📄 Имя файла: prizma-premium-report-' + telegramId + '.pdf\n\n' +
                        '💡 Если скачивание не началось автоматически, проверьте настройки браузера.'
                    );
                }
            }
            
            // Скачиваем отчет
            const result = await DownloadUtils.downloadReport(telegramId, reportType, {
                showInstructions: true
            });
            
            console.log('📊 Результат скачивания:', result);
            
            // Скрываем индикатор загрузки
            if (window.UIHelpers && window.UIHelpers.hideLoadingIndicator) {
                UIHelpers.hideLoadingIndicator();
            }
            
            // Тактильная обратная связь (используем правильные параметры)
            if (reportType === 'premium') {
                window.TelegramWebApp?.hapticFeedback('heavy');
            } else {
                window.TelegramWebApp?.hapticFeedback('light');
            }
            
        } catch (error) {
            console.error('❌ Ошибка при скачивании отчета:', error);
            console.error('❌ Stack trace:', error.stack);
            
            if (window.UIHelpers && window.UIHelpers.hideLoadingIndicator) {
                UIHelpers.hideLoadingIndicator();
            }
            
            window.TelegramWebApp?.showAlert('Ошибка при скачивании отчета: ' + error.message);
        }
    },

    /**
     * Запуск премиум платежа
     */
    async startPremiumPayment() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            console.log('💳 Запуск премиум платежа');
            
            // Показываем индикатор загрузки
            UIHelpers.showLoadingIndicator();
            
            // Запускаем платеж
            const paymentUrl = await ApiClient.startPremiumPayment(telegramId);
            
            // Скрываем индикатор загрузки
            UIHelpers.hideLoadingIndicator();
            
            // Открываем ссылку на платеж
            if (window.TelegramWebApp) {
                window.TelegramWebApp.openLink(paymentUrl);
            } else {
                window.open(paymentUrl, '_blank');
            }
            
        } catch (error) {
            console.error('❌ Ошибка при запуске платежа:', error);
            UIHelpers.hideLoadingIndicator();
            window.TelegramWebApp?.showAlert('Ошибка при запуске платежа');
        }
    },

    /**
     * Проверка статуса пользователя при загрузке
     */
    async checkUserStatusOnLoad() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            const status = await ApiClient.getReportsStatus(telegramId);
            console.log('📊 Статус отчетов:', status);
            console.log('📊 available_report:', status.available_report);
            console.log('📊 free_report:', status.free_report);
            console.log('📊 premium_report:', status.premium_report);
            console.log('📊 status.status:', status.status);
            
            // Если тест не завершен, перенаправляем на страницу с вопросами
            if (status.status === 'test_not_completed') {
                console.log('❌ Тест не завершен, перенаправляем на страницу с вопросами');
                window.location.href = 'question.html';
                return;
            }

            // Логика назначения страниц: download.html только для премиума
            // Если готов премиум — остаемся здесь. Если готов только free — редирект на price-offer
            if (status.available_report && status.available_report.status === 'ready') {
                if (status.available_report.type === 'premium') {
                    console.log('💎 Премиум отчет готов, остаемся на download');
                    // Обновляем текст кнопки для премиум отчета
                    this.updateDownloadButtonForPremium();
                    return;
                } else if (status.available_report.type === 'free') {
                    console.log('🆓 Готов только бесплатный отчет — перенаправляем на price-offer');
                    window.location.href = 'price-offer.html';
                    return;
                }
            }

            // Если есть явный ready free_report — также отправляем на price-offer
            if (status.free_report && status.free_report.status === 'ready') {
                console.log('🆓 Бесплатный отчет готов — перенаправляем на price-offer');
                window.location.href = 'price-offer.html';
                return;
            }

            console.log('❌ Отчет не готов, перенаправляем на loading');
            window.location.href = 'loading.html';
            return
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса отчетов:', error);
        }
    },

    /**
     * Обновить кнопку скачивания для премиум отчета
     */
    updateDownloadButtonForPremium() {
        try {
            const downloadButton = document.getElementById('downloadReport');
            if (downloadButton) {
                const downloadText = downloadButton.querySelector('.download-file-text span');
                if (downloadText) {
                    downloadText.textContent = 'Скачать премиум отчет';
                }
                console.log('💎 Кнопка скачивания обновлена для премиум отчета');
            }
        } catch (error) {
            console.error('❌ Ошибка при обновлении кнопки скачивания:', error);
        }
    }
}; 