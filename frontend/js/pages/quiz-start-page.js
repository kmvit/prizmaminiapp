/**
 * Страница начала теста (Quiz Start Page)
 * Обработка формы входа, валидация и переход к вопросам
 */

const QuizStartPage = {
    /**
     * Инициализация страницы
     */
    async init() {
        console.log('🚀 Инициализация Quiz Start Page');
        
        // Проверяем статус пользователя и перенаправляем при необходимости
        const shouldRedirect = await this.checkUserStatus();
        if (shouldRedirect) {
            return; // Перенаправление уже выполнено
        }
        
        // Настраиваем обработчики событий
        this.setupEventHandlers();
        
        if (!this.isIndex2Page()) {
            this.initCustomSelect();
            await this.loadUserProfile();
            await this.initTimer();
        }
    },

    /**
     * Инициализация кастомного селекта
     */
    initCustomSelect() {
        const selectSelected = $('.select-selected');
        const selectOptions = $('.select-options');
        
        // Открытие/закрытие селекта
        selectSelected.on('click', function(e) {
            e.stopPropagation();
            selectOptions.toggle();
            $(this).toggleClass('select-arrow-active');
        });
        
        // Выбор опции
        $('.option').on('click', function() {
            const value = $(this).data('value');
            const text = $(this).text();
            
            $('#genderInput').val(value);
            $('.select-placeholder').text(text);
            selectOptions.hide();
            selectSelected.removeClass('select-arrow-active');
        });
        
        // Закрытие при клике вне селекта
        $(document).on('click', function() {
            selectOptions.hide();
            selectSelected.removeClass('select-arrow-active');
        });
    },

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        // Кнопка начала теста (на index — форма; на index2 — роут по статусу)
        $('#startTestButton').on('click', (e) => {
            e.preventDefault();
            if (this.isIndex2Page()) {
                this.handleIndex2Continue();
            } else {
                this.startTest();
            }
        });
        
        // Валидация полей при вводе
        $('#nameInput, #ageInput').on('input', () => {
            this.validateForm();
        });
        
        // Обработка кнопки оплаты для активного предложения (со скидкой)
        $('#buyDiscountButton').off('click').on('click', async (e) => {
            e.preventDefault();
            await this.handlePayment(e.currentTarget);
        });
        
        // Обработка кнопки оплаты для истекшего предложения (полная цена)
        $('#buyRegularButton').off('click').on('click', async (e) => {
            e.preventDefault();
            await this.handlePayment(e.currentTarget);
        });
    },

    /**
     * Валидация формы
     */
    validateForm() {
        const name = $('#nameInput').val().trim();
        const age = $('#ageInput').val();
        const gender = $('#genderInput').val();
        
        const isValid = name.length > 0 && age > 0 && age < 120 && gender;
        
        if (isValid) {
            $('#startTestButton').removeClass('disabled');
        } else {
            $('#startTestButton').addClass('disabled');
        }
        
        return isValid;
    },

    /**
     * Загрузить профиль пользователя
     */
    async loadUserProfile() {
        try {
            const telegramId = window.TelegramWebApp?.getUserId();
            if (!telegramId) return;
            
            const profile = await ApiClient.getUserProfile(telegramId);
            
            if (profile && profile.user) {
                // Заполняем форму существующими данными
                if (profile.user.name) {
                    $('#nameInput').val(profile.user.name);
                }
                if (profile.user.age) {
                    $('#ageInput').val(profile.user.age);
                }
                if (profile.user.gender) {
                    $('#genderInput').val(profile.user.gender);
                    const genderText = profile.user.gender === 'male' ? 'Мужской' : 'Женский';
                    $('.select-placeholder').text(genderText);
                }
                
                this.validateForm();
            }
        } catch (error) {
            console.log('ℹ️ Профиль пользователя еще не создан');
        }
    },

    /**
     * Обработка «Продолжить или начать тест» на index2 — переход на нужную страницу
     */
    async handleIndex2Continue() {
        try {
            const telegramId = this.getTelegramUserId();
            if (!telegramId) {
                window.location.href = 'login.html';
                return;
            }
            const reportsStatus = await ApiClient.getReportsStatus(telegramId);
            const freeStatus = reportsStatus.free_report_status;
            const premiumStatus = reportsStatus.premium_report_status;

            if ((premiumStatus?.status === 'processing') || (freeStatus?.status === 'processing') ||
                (reportsStatus.available_report?.status === 'processing')) {
                window.location.href = 'loading.html';
                return;
            }
            if (reportsStatus.available_report?.status === 'ready') {
                if (reportsStatus.available_report.type === 'premium') {
                    window.location.href = 'download.html';
                } else {
                    window.location.href = 'price-offer.html';
                }
                return;
            }
            if (reportsStatus.status === 'success') {
                window.location.href = 'loading.html';
                return;
            }
            // Нет отчёта — идём к вопросам (продолжить тест или начать премиум)
            const progress = await ApiClient.getUserProgress(telegramId);
            const answered = progress?.progress?.answered ?? 0;
            const total = progress?.progress?.total ?? 0;
            if (answered > 0 && answered < total) {
                window.location.href = 'question.html';
            } else {
                window.location.href = 'question.html'; // начать тест
            }
        } catch (error) {
            console.error('❌ Ошибка handleIndex2Continue:', error);
            window.location.href = 'question.html';
        }
    },

    /**
     * Начать тест
     */
    async startTest() {
        if (!this.validateForm()) {
            window.TelegramWebApp?.showAlert('Пожалуйста, заполните все поля');
            return;
        }
        
        const name = $('#nameInput').val().trim();
        const age = parseInt($('#ageInput').val());
        const gender = $('#genderInput').val();
        
        try {
            const telegramId = window.TelegramWebApp?.getUserId();
            if (!telegramId) {
                console.error('❌ Не удалось получить Telegram ID');
                window.location.href = 'login.html';
                return;
            }
            
            // Сохраняем профиль пользователя
            await ApiClient.saveUserProfile(telegramId, {
                name: name,
                age: age,
                gender: gender
            });
            
            console.log('✅ Профиль сохранен, переход к вопросам');
            
            // Тактильная обратная связь
            window.TelegramWebApp?.hapticFeedback('light');
            
            // Переход на страницу вопросов
            window.location.href = 'question.html';
            
        } catch (error) {
            console.error('❌ Ошибка при сохранении профиля:', error);
            window.TelegramWebApp?.showAlert('Ошибка при сохранении данных. Попробуйте еще раз.');
        }
    },

    /**
     * Инициализация таймера спецпредложения
     */
    async initTimer() {
        try {
            console.log('⏰ Запуск таймера спецпредложения');
            
            const telegramId = window.TelegramWebApp?.getUserId();
            if (!telegramId) {
                console.log('ℹ️ Telegram ID не найден, таймер не запущен');
                return;
            }

            // Получаем информацию о таймере с сервера
            const timerData = await ApiClient.getSpecialOfferTimer(telegramId);
            
            if (timerData.status === 'success' && timerData.timer) {
                this.updateTimerDisplay(timerData.timer, timerData.pricing);
                this.startCountdown(timerData.timer.remaining_seconds);
            } else {
                console.error('❌ Ошибка получения таймера:', timerData);
                this.updateTimerDisplay({ time_string: '23:59:59', is_expired: false });
            }
        } catch (error) {
            console.error('❌ Ошибка запуска таймера:', error);
            this.updateTimerDisplay({ time_string: '23:59:59', is_expired: false });
        }
    },

    /**
     * Обновление отображения таймера и цены
     */
    updateTimerDisplay(timer, pricing = null) {
        const timeElement = document.querySelector('.decoding-offer-time');
        const timeElementExpired = document.getElementById('timerDisplayExpired');
        
        if (timeElement) {
            timeElement.textContent = timer.time_string;
            
            // Если время истекло, показываем 00:00:00 и переключаем блоки
            if (timer.is_expired) {
                timeElement.textContent = '00:00:00';
                timeElement.style.color = '#ff4444'; // Красный цвет для истекшего времени
                
                // Обновляем таймер в блоке истекшего предложения
                if (timeElementExpired) {
                    timeElementExpired.textContent = '00:00:00';
                    timeElementExpired.style.color = '#ff4444';
                }
                
                // Показываем блок с истекшим предложением
                const promoActive = document.getElementById('promoActive');
                const promoExpired = document.getElementById('promoExpired');
                if (promoActive && promoExpired) {
                    promoActive.style.display = 'none';
                    promoExpired.style.display = 'block';
                }
            } else {
                timeElement.style.color = ''; // Возвращаем обычный цвет
                
                // Показываем блок с активным предложением
                const promoActive = document.getElementById('promoActive');
                const promoExpired = document.getElementById('promoExpired');
                if (promoActive && promoExpired) {
                    promoActive.style.display = 'block';
                    promoExpired.style.display = 'none';
                }
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
        // Обновляем цену в обоих блоках (активном и истекшем)
        const currentPriceElements = document.querySelectorAll('.decoding-offer-button-current-price');
        const oldPriceElements = document.querySelectorAll('.decoding-offer-button-old-price');
        
        // Обновляем все элементы с текущей ценой
        currentPriceElements.forEach(element => {
            element.textContent = `${pricing.current_price.toLocaleString()}р`;
        });
        
        // Обновляем все элементы со старой ценой
        oldPriceElements.forEach(element => {
            if (pricing.is_offer_active) {
                // Показываем старую цену зачеркнутой
                element.innerHTML = `<span>${pricing.original_price.toLocaleString()}р</span>`;
                element.style.display = 'block';
            } else {
                // Скрываем старую цену, если спецпредложение истекло
                element.style.display = 'none';
            }
        });
        
        console.log(`💰 Цена обновлена: ${pricing.current_price}р (спецпредложение: ${pricing.is_offer_active ? 'активно' : 'истекло'})`);
    },

    /**
     * Запустить обратный отсчет
     */
    startCountdown(remainingSeconds) {
        let totalSeconds = remainingSeconds;
        const timeElement = document.querySelector('.decoding-offer-time');
        const timeElementExpired = document.getElementById('timerDisplayExpired');
        
        if (!timeElement) {
            console.error('❌ Элемент таймера не найден');
            return;
        }

        const updateCountdown = () => {
            if (totalSeconds <= 0) {
                // Время истекло
                timeElement.textContent = '00:00:00';
                timeElement.style.color = '#ff4444';
                
                if (timeElementExpired) {
                    timeElementExpired.textContent = '00:00:00';
                    timeElementExpired.style.color = '#ff4444';
                }
                
                console.log('⏰ Время спецпредложения истекло');
                
                // Показываем блок с истекшим предложением
                const promoActive = document.getElementById('promoActive');
                const promoExpired = document.getElementById('promoExpired');
                if (promoActive && promoExpired) {
                    promoActive.style.display = 'none';
                    promoExpired.style.display = 'block';
                }
                
                // Обновляем цену на полную (если нужно)
                // ВАЖНО: Реальные цены приходят через API из .env
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
    },

    /**
     * Обработка платежа (общий метод для обеих кнопок)
     */
    async handlePayment(buttonElement) {
        this.safeHapticFeedback('medium');
        
        const $button = $(buttonElement);
        const originalText = $button.html();
        const telegramId = this.getTelegramUserId();
        
        if (!telegramId) {
            this.safeShowAlert('Ошибка: не удалось получить ID пользователя');
            return;
        }
        
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
    },

    /**
     * Получение Telegram ID пользователя
     */
    getTelegramUserId() {
        return window.TelegramWebApp ? window.TelegramWebApp.getUserId() : null;
    },

    /**
     * Безопасная тактильная обратная связь
     */
    safeHapticFeedback(type = 'light') {
        if (window.TelegramWebApp) {
            try {
                window.TelegramWebApp.hapticFeedback(type);
            } catch (error) {
                console.log('ℹ️ Тактильная обратная связь недоступна');
            }
        }
    },

    /**
     * Безопасное отображение алерта
     */
    safeShowAlert(message) {
        if (window.TelegramWebApp && window.TelegramWebApp.showAlert) {
            window.TelegramWebApp.showAlert(message);
        } else {
            alert(message);
        }
    },

    /**
     * На index2 не делаем редирект — мы уже на нужной странице
     */
    isIndex2Page() {
        return window.location.pathname.includes('index2') || window.location.href.includes('index2');
    },

    /**
     * Проверка статуса пользователя
     * Возвращает true, если было выполнено перенаправление
     */
    async checkUserStatus() {
        try {
            const telegramId = this.getTelegramUserId();
            if (!telegramId) {
                console.log('ℹ️ Telegram ID не найден, пропускаем проверку статуса');
                return false;
            }

            // На index2 — не редиректим (возвращающийся пользователь уже на нужной странице)
            if (this.isIndex2Page()) {
                console.log('📄 Страница index2 — пропускаем редирект');
                return false;
            }

            console.log('🔍 Проверяем статус пользователя:', telegramId);
            
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
                    console.log('✅ Все вопросы завершены — перенаправляем на index2 (возвращающийся пользователь)');
                    window.location.href = 'index2.html';
                    return true;
                }
                if (answered > 0) {
                    console.log('📝 Есть незавершенные вопросы, перенаправляем на question');
                    window.location.href = 'question.html';
                    return true;
                }

                console.log('🆕 Новый пользователь, остаемся на главной странице');
                return false;
            }
            
            // Пользователь с пройденными тестами — при повторном входе показываем index2
            const freeStatus = reportsStatus.free_report_status;
            const premiumStatus = reportsStatus.premium_report_status;
            if ((premiumStatus && premiumStatus.status === 'processing') || 
                (freeStatus && freeStatus.status === 'processing') || 
                (reportsStatus.available_report && reportsStatus.available_report.status === 'processing')) {
                console.log('⏳ Отчет генерируется — перенаправляем на index2');
                window.location.href = 'index2.html';
                return true;
            }
            
            if (reportsStatus.available_report && reportsStatus.available_report.status === 'ready') {
                console.log('✅ Отчет готов (free или premium) — перенаправляем на index2');
                window.location.href = 'index2.html';
                return true;
            }
            
            if (reportsStatus.status === 'success' && 
                (!reportsStatus.available_report || reportsStatus.available_report.status !== 'ready')) {
                console.log('✅ Тест завершен — перенаправляем на index2');
                window.location.href = 'index2.html';
                return true;
            }
            
            console.log('🆕 Новый пользователь или статус не определен, остаемся на главной странице');
            return false;
            
        } catch (error) {
            console.error('❌ Ошибка при проверке статуса пользователя:', error);
            // В случае ошибки остаемся на странице
            return false;
        }
    }
};

// Инициализация при загрузке страницы
$(document).ready(() => {
    QuizStartPage.init();
});
