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
        
        // Даем время на инициализацию Telegram WebApp
        setTimeout(() => {
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
        }, 200); // Небольшая задержка для инициализации
    },

    /**
     * Настройка Telegram UI для страницы вопросов
     */
    setupTelegramUI() {
        if (window.TelegramWebApp) {
            try {
                if (window.TelegramWebApp.showBackButton) {
                    window.TelegramWebApp.showBackButton(() => {
                        window.location.href = 'login.html';
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
        UIHelpers.setupTextareaFocus();
    },

    /**
     * Проверка заполненности профиля
     * Если профиль неполный, перенаправляем на login.html
     */
    async ensureProfileOrRedirect() {
        try {
            const telegramId = this.getTelegramUserId();
            console.log('👤 Проверяем профиль для пользователя:', telegramId);
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
     * Получение Telegram ID пользователя
     */
    getTelegramUserId() {
        let telegramId = 123456789; // Дефолтное значение для тестирования
        
        try {
            if (window.TelegramWebApp && typeof window.TelegramWebApp.getUserId === 'function') {
                telegramId = window.TelegramWebApp.getUserId();
            } else if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
                telegramId = window.Telegram.WebApp.initDataUnsafe.user.id;
            }
            
            console.log('👤 Получен Telegram ID:', telegramId);
            return telegramId;
        } catch (error) {
            console.error('❌ Ошибка получения Telegram ID:', error);
            return 123456789; // Fallback
        }
    },

    /**
     * Загрузка текущего вопроса
     */
    async loadCurrentQuestion() {
        try {
            const telegramId = this.getTelegramUserId();
            console.log('🔄 Загружаем вопрос для пользователя:', telegramId);
            
            const questionData = await ApiClient.getCurrentQuestion(telegramId);
            console.log('📥 Получены данные вопроса:', questionData);
            
            if (questionData) {
                if (questionData.question) {
                    this.displayQuestion(questionData);
                } else {
                    console.log('❌ В ответе нет поля question — проверяем оплату и перенаправляем при необходимости');
                    const redirected = await this.redirectToOfferIfUnpaid(telegramId);
                    if (!redirected) {
                        // Если оплата завершена или профиль недоступен — переходим к загрузке/завершению
                        window.location.href = 'loading.html';
                    }
                }
            } else {
                console.log('❌ Нет доступных вопросов — проверяем оплату и перенаправляем при необходимости');
                const redirected = await this.redirectToOfferIfUnpaid(telegramId);
                if (!redirected) {
                    window.location.href = 'loading.html';
                }
            }
        } catch (error) {
            console.error('❌ Ошибка при загрузке вопроса:', error);
            console.error('❌ Детали ошибки:', error.message, error.stack);
            
            // Проверяем, завершен ли тест
            if (error.message && error.message.includes('Test already completed')) {
                console.log('✅ Тест завершен, перенаправляем на loading');
                window.location.href = 'loading.html';
                return;
            }
            
            // Проверяем другие ошибки
            if (error.message && error.message.includes('Test already completed')) {
                console.log('✅ Тест завершен, перенаправляем на loading');
                window.location.href = 'loading.html';
                return;
            }
            
            // При ошибке пробуем перенаправить на оффер, если премиум не оплачен
            try {
                const telegramId = this.getTelegramUserId();
                const redirected = await this.redirectToOfferIfUnpaid(telegramId);
                if (redirected) return;
            } catch (_) {}

            // Показываем пользователю сообщение об ошибке
            $('#questionText').text('Ошибка загрузки вопроса. Попробуйте обновить страницу.');
            $('.current-question').text('?');
            $('.question-count').text('?');
        }
    },

    /**
     * Отображение вопроса
     */
    displayQuestion(data) {
        console.log('📋 Отображаем данные вопроса:', JSON.stringify(data, null, 2));
        
        // Проверяем структуру данных
        if (!data) {
            console.error('❌ Нет данных вопроса');
            return;
        }
        
        if (!data.question) {
            console.error('❌ Нет объекта question в данных:', data);
            return;
        }
        
        if (!data.progress) {
            console.error('❌ Нет объекта progress в данных:', data);
            return;
        }
        
        // Проверяем наличие элементов DOM
        const questionTextElement = $('#questionText');
        const currentQuestionElement = $('.current-question');
        const questionCountElement = $('.question-count');
        
        console.log('🔍 Проверка элементов DOM:');
        console.log('  - questionText найден:', questionTextElement.length > 0);
        console.log('  - current-question найден:', currentQuestionElement.length > 0);
        console.log('  - question-count найден:', questionCountElement.length > 0);
        
        // Обновляем текст вопроса
        if (questionTextElement.length > 0) {
            questionTextElement.text(data.question.text);
            console.log('📝 Установлен текст вопроса:', data.question.text);
        } else {
            console.error('❌ Элемент #questionText не найден');
        }
        
        // Обновляем номер текущего вопроса
        if (currentQuestionElement.length > 0) {
            currentQuestionElement.text(data.progress.current);
            console.log('🔢 Установлен номер вопроса:', data.progress.current);
        } else {
            console.error('❌ Элемент .current-question не найден');
        }
        
        // Обновляем общее количество вопросов
        if (questionCountElement.length > 0) {
            questionCountElement.text(data.progress.total);
            console.log('📊 Установлено общее количество:', data.progress.total);
        } else {
            console.error('❌ Элемент .question-count не найден');
        }
    },

    /**
     * Обновление состояния кнопки в зависимости от количества символов
     */
    updateButtonState() {
        const answerText = $('#questionArea').val().trim();
        const minLength = 350;
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
            if (answerText.length >= 350) {
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
                if (answerText.length >= 350) {
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
     * Проверить статус оплаты и при отсутствии оплаты перекинуть на экран оффера
     * @param {number} telegramId
     * @returns {Promise<boolean>} true если был выполнен редирект
     */
    async redirectToOfferIfUnpaid(telegramId) {
        try {
            const profile = await ApiClient.getUserProfile(telegramId);
            const paymentStatus = profile && (profile.payment_status || profile?.user?.payment_status);
            console.log('💳 Статус оплаты:', paymentStatus);
            if (paymentStatus !== 'completed') {
                console.log('➡️ Переадресуем на экран спецпредложения (price-offer)');
                window.location.href = 'price-offer.html';
                return true;
            }
        } catch (e) {
            console.warn('⚠️ Не удалось получить профиль для проверки оплаты:', e);
        }
        return false;
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
            if (answer.length < 350) {
                console.log('❌ Ответ слишком короткий:', answer.length, 'символов');
                window.TelegramWebApp?.showAlert('Ответ должен содержать минимум 350 символов');
                return;
            }

            const telegramId = this.getTelegramUserId();
            
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
            // Для бесплатных пользователей проверяем free_questions_limit, для премиум - total
            const isFreeUser = !progress.user || !progress.user.is_paid;
            const questionsLimit = isFreeUser ? progress.progress.free_questions_limit : progress.progress.total;
            
            if (progress.progress.answered >= questionsLimit) {
                console.log('✅ Пользователь завершил вопросы, переходим на loading.html');
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