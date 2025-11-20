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
        this.startSpecialOfferTimer();
    },

    /**
     * Настройка Telegram UI для страницы спецпредложения
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            try { window.TelegramWebApp.forceBackButtonVisibility(false); } catch (_) {}
            try {
                window.TelegramWebApp.showMainButton('Закрыть', () => {
                    try { window.TelegramWebApp.close(); } catch (e) { try { window.close(); } catch (e2) {} }
                });
            } catch (_) {}
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
            
            // Если пользователь вернулся после неуспешной оплаты, сохраняем состояние акции
            if (status.payment_status === 'failed' || !status.payment_status) {
                console.log('🔄 Пользователь вернулся после неуспешной оплаты, восстанавливаем акцию');
                // Сохраняем информацию о том, что пользователь был на акции
                localStorage.setItem('was_on_special_offer', 'true');
                localStorage.setItem('special_offer_timestamp', Date.now().toString());
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
    },

    /**
     * Запуск таймера спецпредложения
     */
    async startSpecialOfferTimer() {
        try {
            console.log('⏰ Запуск таймера спецпредложения');
            
            const telegramId = this.getTelegramUserId();
            if (!telegramId) {
                console.error('❌ Не удалось получить Telegram ID');
                return;
            }

            // Проверяем, был ли пользователь на акции ранее (после неуспешной оплаты)
            const wasOnSpecialOffer = localStorage.getItem('was_on_special_offer') === 'true';
            const specialOfferTimestamp = localStorage.getItem('special_offer_timestamp');
            
            if (wasOnSpecialOffer && specialOfferTimestamp) {
                const timeSinceReturn = Date.now() - parseInt(specialOfferTimestamp);
                // Если прошло меньше 5 минут с момента возврата, восстанавливаем акцию
                if (timeSinceReturn < 5 * 60 * 1000) {
                    console.log('🔄 Восстанавливаем акцию после неуспешной оплаты');
                    // Очищаем флаги
                    localStorage.removeItem('was_on_special_offer');
                    localStorage.removeItem('special_offer_timestamp');
                }
            }

            // Получаем информацию о таймере с сервера
            const timerData = await ApiClient.getSpecialOfferTimer(telegramId);
            
            if (timerData.status === 'success' && timerData.timer) {
                // Обновляем таймер и цену
                this.updateTimerDisplay(timerData.timer, timerData.pricing);
                this.startCountdown(timerData.timer.remaining_seconds);
            } else {
                console.error('❌ Ошибка получения таймера:', timerData);
                // Если таймер не найден, но пользователь был на акции, показываем акцию
                // ВАЖНО: Эти значения используются только при ошибке API. Реальные цены приходят через API из .env
                if (wasOnSpecialOffer) {
                    console.log('💎 Показываем акцию для пользователя, который был на ней ранее');
                    this.updateTimerDisplay({ time_string: '23:59:59', is_expired: false });
                    this.updatePricingDisplay({
                        current_price: 1,  // Fallback значение - реальная цена приходит через API
                        original_price: 1,  // Fallback значение - реальная цена приходит через API
                        is_offer_active: true
                    });
                }
            }
            
        } catch (error) {
            console.error('❌ Ошибка запуска таймера:', error);
            // Показываем статичное время в случае ошибки
            this.updateTimerDisplay({ time_string: '23:59:59', is_expired: false });
        }
    },

    /**
     * Обновление отображения таймера и цены
     */
    updateTimerDisplay(timer, pricing = null) {
        const timeElement = document.querySelector('.decoding-offer-time');
        if (timeElement) {
            timeElement.textContent = timer.time_string;
            
            // Если время истекло, показываем 00:00:00
            if (timer.is_expired) {
                timeElement.textContent = '00:00:00';
                timeElement.style.color = '#ff4444'; // Красный цвет для истекшего времени
            } else {
                timeElement.style.color = ''; // Возвращаем обычный цвет
            }
        }
        
        // Обновляем цену, если передана информация о ценообразовании
        if (pricing) {
            this.updatePricingDisplay(pricing);
        }
    },

    /**
     * Обновление отображения цены
     */
    updatePricingDisplay(pricing) {
        const currentPriceElement = document.querySelector('.decoding-offer-button-current-price');
        const oldPriceElement = document.querySelector('.decoding-offer-button-old-price');
        
        if (currentPriceElement) {
            currentPriceElement.textContent = `${pricing.current_price.toLocaleString()}р`;
        }
        
        if (oldPriceElement) {
            if (pricing.is_offer_active) {
                // Показываем старую цену зачеркнутой
                oldPriceElement.innerHTML = `вместо <span>${pricing.original_price.toLocaleString()}р</span>`;
                oldPriceElement.style.display = 'block';
            } else {
                // Скрываем старую цену, если спецпредложение истекло
                oldPriceElement.style.display = 'none';
            }
        }
        
        console.log(`💰 Цена обновлена: ${pricing.current_price}р (спецпредложение: ${pricing.is_offer_active ? 'активно' : 'истекло'})`);
    },

    /**
     * Запуск обратного отсчета
     */
    startCountdown(remainingSeconds) {
        let totalSeconds = remainingSeconds;
        const timeElement = document.querySelector('.decoding-offer-time');
        
        if (!timeElement) {
            console.error('❌ Элемент таймера не найден');
            return;
        }

        const updateCountdown = () => {
            if (totalSeconds <= 0) {
                // Время истекло
                timeElement.textContent = '00:00:00';
                timeElement.style.color = '#ff4444';
                console.log('⏰ Время спецпредложения истекло');
                
                // Обновляем цену на полную
                // ВАЖНО: Эти значения используются только при истечении таймера на клиенте. Реальные цены приходят через API из .env
                this.updatePricingDisplay({
                    current_price: 1,  // Fallback значение - реальная цена приходит через API
                    original_price: 1,  // Fallback значение - реальная цена приходит через API
                    is_offer_active: false
                });
                return;
            }

            // Вычисляем часы, минуты и секунды
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;

            // Форматируем время
            const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            timeElement.textContent = timeString;
            totalSeconds--;

            // Продолжаем отсчет каждую секунду
            setTimeout(updateCountdown, 1000);
        };

        // Запускаем отсчет
        updateCountdown();
    }
}; 