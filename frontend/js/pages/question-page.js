/**
 * Страница вопросов (question.html)
 * Инициализация и логика страницы вопросов
 */

'use strict';

// Создаем глобальный объект для страницы вопросов
window.QuestionPage = {
    /**
     * Инициализация страницы вопросов
     */
    init() {
        console.log('❓ Инициализация страницы вопросов');
        
        // Сначала проверяем заполненность профиля. Если не заполнен — редирект на login
        this.ensureProfileOrRedirect().then((ok) => {
            if (!ok) return;

            this.setupTelegramUI();
            this.setupUI();
            this.loadCurrentQuestion();
            this.setupEventHandlers();
            
            // Инициализируем состояние кнопки
            this.updateButtonState();
        });
    },

    /**
     * Настройка Telegram UI для страницы вопросов
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showBackButton(() => {
                window.location.href = 'login.html';
            });
            window.TelegramWebApp.hideMainButton();
        }
    },

    /**
     * Настройка UI элементов
     */
    setupUI() {
        UIHelpers.setupTextareaFocus();
    },

    /**
     * Проверка заполненности профиля
     * Если профиль неполный, перенаправляем на login.html
     */
    async ensureProfileOrRedirect() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            const profile = await ApiClient.getUserProfile(telegramId);
            const user = profile && profile.user ? profile.user : null;
            const hasName = !!(user && user.name && String(user.name).trim());
            const hasAge = !!(user && typeof user.age === 'number' && user.age > 0);
            const hasGender = !!(user && user.gender);

            if (!hasName || !hasAge || !hasGender) {
                console.log('👤 Профиль не заполнен, перенаправляем на login');
                window.location.href = 'login.html';
                return false;
            }
            return true;
        } catch (error) {
            console.error('❌ Ошибка при проверке профиля:', error);
            // В случае ошибки подстраховываемся и отправляем на login
            window.location.href = 'login.html';
            return false;
        }
    },

    /**
     * Загрузка текущего вопроса
     */
    async loadCurrentQuestion() {
        try {
            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            const questionData = await ApiClient.getCurrentQuestion(telegramId);
            
            if (questionData) {
                this.displayQuestion(questionData);
            } else {
                console.log('❌ Нет доступных вопросов');
                window.location.href = 'loading.html';
            }
        } catch (error) {
            console.error('❌ Ошибка при загрузке вопроса:', error);
        }
    },

    /**
     * Отображение вопроса
     */
    displayQuestion(data) {
        // Обновляем текст вопроса
        $('#questionText').text(data.question.text);
        
        // Обновляем номер текущего вопроса
        $('.current-question').text(data.progress.current);
        
        // Обновляем общее количество вопросов
        $('.question-count').text(data.progress.total);
    },

    /**
     * Обновление состояния кнопки в зависимости от количества символов
     */
    updateButtonState() {
        const answerText = $('#questionArea').val().trim();
        const minLength = 500;
        const currentLength = answerText.length;
        
        // Обновляем счетчик символов
        $('#currentCount').text(currentLength);
        
        // Обновляем стиль счетчика
        const counter = $('#characterCounter');
        if (currentLength >= minLength) {
            counter.removeClass('invalid').addClass('valid');
        } else {
            counter.removeClass('valid').addClass('invalid');
        }
        
        // Обновляем состояние кнопки
        if (currentLength >= minLength) {
            $('#nextButton').prop('disabled', false).removeClass('disabled');
            $('#nextButton span').text('Следующий вопрос');
        } else {
            $('#nextButton').prop('disabled', true).addClass('disabled');
            const remaining = minLength - currentLength;
            $('#nextButton span').text(`Еще ${remaining} символов`);
        }
    },

    /**
     * Настройка обработчиков событий
     */
    setupEventHandlers() {
        // Обработчик отправки ответа
        $('#nextButton').on('click', () => {
            const answerText = $('#questionArea').val().trim();
            if (answerText.length >= 500) {
                this.submitAnswer();
            }
        });



        // Обработчик закрытия модального окна
        $('#modalClose').on('click', () => {
            this.hideWelcomeModal();
        });

        // Обработчик закрытия модального окна по клику на оверлей
        $('#welcomeModal').on('click', (e) => {
            if (e.target.id === 'welcomeModal') {
                this.hideWelcomeModal();
            }
        });

        // Обработка Enter в textarea
        $('#questionArea').on('keydown', (e) => {
            if (e.ctrlKey && e.keyCode === 13) {
                const answerText = $('#questionArea').val().trim();
                if (answerText.length >= 500) {
                    this.submitAnswer();
                }
            }
        });

        // Обработка изменений в textarea для обновления состояния кнопки
        $('#questionArea').on('input', () => {
            this.updateButtonState();
        });

        // Показываем модальное окно только при первом посещении
        this.checkAndShowWelcomeModal();
    },



    /**
     * Проверить и показать модальное окно приветствия только при первом посещении
     */
    checkAndShowWelcomeModal() {
        const hasSeenWelcome = localStorage.getItem('prizma_welcome_seen');
        
        if (!hasSeenWelcome) {
            console.log('👋 Первое посещение - показываем модальное окно приветствия');
            this.showWelcomeModal();
            // Отмечаем, что модальное окно уже было показано
            localStorage.setItem('prizma_welcome_seen', 'true');
        } else {
            console.log('👋 Модальное окно уже было показано ранее');
        }
    },

    /**
     * Показать модальное окно приветствия
     */
    showWelcomeModal() {
        console.log('👋 Показываем модальное окно приветствия');
        $('#welcomeModal').addClass('show');
        
        // Тактильная обратная связь
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hapticFeedback('light');
        }
    },

    /**
     * Скрыть модальное окно приветствия
     */
    hideWelcomeModal() {
        console.log('👋 Скрываем модальное окно приветствия');
        $('#welcomeModal').removeClass('show');
        
        // Тактильная обратная связь
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hapticFeedback('light');
        }
    },

    /**
     * Отправка ответа
     */
    async submitAnswer() {
        try {
            const answer = $('#questionArea').val().trim();
            if (!answer) {
                window.TelegramWebApp?.showAlert('Пожалуйста, введите ответ');
                return;
            }

            // Проверка на минимальное количество символов
            if (answer.length < 500) {
                console.log('❌ Ответ слишком короткий:', answer.length, 'символов');
                window.TelegramWebApp?.showAlert('Ответ должен содержать минимум 500 символов');
                return;
            }

            const telegramId = window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
            
            // Показываем индикатор загрузки
            UIHelpers.showLoadingIndicator();
            
            // Отправляем ответ
            await ApiClient.submitAnswer(telegramId, answer);
            
            // Скрываем индикатор загрузки
            UIHelpers.hideLoadingIndicator();
            
            // Тактильная обратная связь
            window.TelegramWebApp?.hapticFeedback('success');
            
            // Перенаправляем на следующий вопрос или на загрузку
            const progress = await ApiClient.getUserProgress(telegramId);
            if (progress.progress.answered >= progress.progress.total) {
                window.location.href = 'loading.html';
            } else {
                // Перезагружаем страницу для следующего вопроса
                window.location.reload();
            }
            
        } catch (error) {
            console.error('❌ Ошибка при отправке ответа:', error);
            UIHelpers.hideLoadingIndicator();
            window.TelegramWebApp?.showAlert('Ошибка при отправке ответа');
        }
    }
}; 