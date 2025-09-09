/**
 * Страница входа (login.html)
 * Инициализация и логика страницы входа
 */

'use strict';

// Создаем глобальный объект для страницы входа
window.LoginPage = {
    /**
     * Инициализация страницы входа
     */
    init() {
        console.log('👤 Инициализация страницы входа');
        
        this.setupTelegramUI();
        this.setupUI();
        this.setupEventHandlers();
        this.loadUserProfile();
    },

    /**
     * Настройка Telegram UI для страницы входа
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            try {
                if (window.TelegramWebApp.showBackButton) {
                    window.TelegramWebApp.showBackButton(() => {
                        window.location.href = 'price.html';
                    });
                }
                if (window.TelegramWebApp.hideMainButton) {
                    window.TelegramWebApp.hideMainButton();
                }
            } catch (error) {
                console.log('⚠️ Ошибка настройки кнопок Telegram:', error);
            }
        }
    },

    /**
     * Настройка UI элементов
     */
    setupUI() {
        // Инициализируем кастомный селект
        this.setupCustomSelect();
    },

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        // Обработчик для кнопки "Продолжить"
        $('#continueButton').on('click', (e) => {
            e.preventDefault();
            console.log('👤 Сохранение профиля пользователя');
            this.saveUserProfile();
        });
    },

    /**
     * Настройка кастомного селекта
     */
    setupCustomSelect() {
        const select = $('.custom-select');
        const selected = select.find('.select-selected');
        const options = select.find('.select-options');
        const hiddenInput = select.find('#genderInput');
        const placeholder = select.find('.select-placeholder');

        selected.on('click', function() {
            options.toggle();
        });

        options.find('.option').on('click', function() {
            const value = $(this).data('value');
            const text = $(this).text();
            
            hiddenInput.val(value);
            placeholder.text(text);
            options.hide();
        });

        // Закрытие при клике вне селекта
        $(document).on('click', function(e) {
            if (!$(e.target).closest('.custom-select').length) {
                options.hide();
            }
        });
    },

    /**
     * Загрузка профиля пользователя
     */
    async loadUserProfile() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            const profile = await ApiClient.getUserProfile(telegramId);
            
            if (profile && profile.user) {
                // Заполняем поля если данные есть
                if (profile.user.name) {
                    $('#nameInput').val(profile.user.name);
                }
                if (profile.user.age) {
                    $('#ageInput').val(profile.user.age);
                }
                if (profile.user.gender) {
                    $('#genderInput').val(profile.user.gender);
                    $('.select-placeholder').text(profile.user.gender === 'male' ? 'Мужской' : 'Женский');
                }
            }
        } catch (error) {
            console.error('❌ Ошибка при загрузке профиля:', error);
        }
    },

    /**
     * Сохранение профиля пользователя
     */
    async saveUserProfile() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            // Получаем данные из формы
            const name = $('#nameInput').val().trim();
            const age = parseInt($('#ageInput').val());
            const gender = $('#genderInput').val();
            
            // Валидация
            if (!name) {
                this.safeShowAlert('Пожалуйста, введите ваше имя');
                return;
            }
            
            if (!age || age < 1 || age > 120) {
                this.safeShowAlert('Пожалуйста, введите корректный возраст');
                return;
            }
            
            if (!gender) {
                this.safeShowAlert('Пожалуйста, выберите пол');
                return;
            }
            
            // Тактильная обратная связь
            this.safeHapticFeedback('light');
            
            console.log('💾 Сохранение профиля:', { name, age, gender });
            
            // Сохраняем профиль
            await ApiClient.saveUserProfile(telegramId, {
                name: name,
                age: age,
                gender: gender
            });
            
            console.log('✅ Профиль сохранен, перенаправляем на вопросы');
            
            // Перенаправляем на вопросы
            window.location.href = 'question.html';
            
        } catch (error) {
            console.error('❌ Ошибка при сохранении профиля:', error);
            this.safeShowAlert('Ошибка при сохранении профиля. Попробуйте еще раз.');
        }
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