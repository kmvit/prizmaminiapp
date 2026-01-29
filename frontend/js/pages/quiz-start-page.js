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
        
        // Инициализируем кастомный селект для пола
        this.initCustomSelect();
        
        // Настраиваем обработчики событий
        this.setupEventHandlers();
        
        // Загружаем данные пользователя если есть
        await this.loadUserProfile();
        
        // Инициализируем таймер спецпредложения
        await this.initTimer();
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
        // Кнопка начала теста
        $('#startTestButton').on('click', (e) => {
            e.preventDefault();
            this.startTest();
        });
        
        // Валидация полей при вводе
        $('#nameInput, #ageInput').on('input', () => {
            this.validateForm();
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
            const telegramId = window.TelegramWebApp?.getUserId();
            if (!telegramId) return;
            
            // Получаем информацию о таймере
            const profile = await ApiClient.getUserProfile(telegramId);
            
            if (profile && profile.user && profile.user.special_offer_started_at) {
                const startTime = new Date(profile.user.special_offer_started_at);
                const now = new Date();
                const elapsed = Math.floor((now - startTime) / 1000); // секунды
                const duration = 12 * 60 * 60; // 12 часов в секундах
                const remaining = duration - elapsed;
                
                if (remaining > 0) {
                    this.startCountdown(remaining);
                } else {
                    this.showExpiredOffer();
                }
            }
        } catch (error) {
            console.log('ℹ️ Таймер еще не запущен');
        }
    },

    /**
     * Запустить обратный отсчет
     */
    startCountdown(seconds) {
        const updateTimer = () => {
            if (seconds <= 0) {
                this.showExpiredOffer();
                return;
            }
            
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            const display = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
            $('#timerDisplay').text(display);
            
            seconds--;
            setTimeout(updateTimer, 1000);
        };
        
        updateTimer();
    },

    /**
     * Показать истекшее предложение
     */
    showExpiredOffer() {
        $('#promoActive').hide();
        $('#promoExpired').show();
    }
};

// Инициализация при загрузке страницы
$(document).ready(() => {
    QuizStartPage.init();
});
