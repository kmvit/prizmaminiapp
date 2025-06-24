'use strict';
$(function() {
    // Существующий код из main.js
    const closedStyle = {
        borderRadius: "25px",
        borderBottomLeftRadius: "25px",
        borderBottomRightRadius: "25px"
    };
    const openedStyle = {
        borderRadius: "25px 25px 0 0",
        borderBottomLeftRadius: "0",
        borderBottomRightRadius: "0"
    };

    let selectSelected = $(".select-selected");
    // Инициализация
    $(".select-selected").css(closedStyle);

    $(".select-selected").click(function(e) {
        e.stopPropagation();
        const isOpen = $("#selectOptions").hasClass("show");

        $("#selectOptions").toggleClass("show");
        $(".custom-arrow").css("transform", isOpen ? "rotate(0)" : "rotate(180deg)");
        $(".select-selected").css(isOpen ? closedStyle : openedStyle);

        // Тактильная обратная связь
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hapticFeedback('light');
        }
    });

    $(".option").click(function() {
        const value = $(this).data("value");
        const text = $(this).text();

        $(".select-placeholder").text(text);
        $("#genderInput").val(value);

        $("#selectOptions").removeClass("show");
        $(".custom-arrow").css("transform", "rotate(0)");
        $(".select-selected").css(closedStyle);

        // Тактильная обратная связь
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hapticFeedback('medium');
        }
    });

    $(document).click(function() {
        if ($("#selectOptions").hasClass("show")) {
            $("#selectOptions").removeClass("show");
            $(".custom-arrow").css("transform", "rotate(0)");
            $(".select-selected").css(closedStyle);
        }
    });

    $("#answers-acc").accordion({
        collapsible: true,
        active: false,
    });

    const textarea = document.querySelector('.question-area');
    const writeIcon = document.querySelector('.write-icon');

    if (textarea && writeIcon) {
        textarea.addEventListener('focus', () => {
            writeIcon.style.visibility = 'hidden';
        });
        textarea.addEventListener('blur', () => {
            writeIcon.style.visibility = 'visible';
        });
    }

    // Telegram Web App специфичный код - инициализация с задержкой
    function initTelegramApp() {
        console.log('🔄 Попытка инициализации TelegramApp...');
        console.log('📱 window.TelegramWebApp:', !!window.TelegramWebApp);
        console.log('📱 window.Telegram:', !!window.Telegram);
        
        if (window.TelegramWebApp && window.TelegramWebApp.tg) {
            // Инициализация для разных страниц
            const currentPage = getCurrentPage();
            console.log('🎯 Current page detected:', currentPage);
            console.log('🔗 Current URL:', window.location.href);
            
            switch(currentPage) {
                case 'index':
                    initIndexPage();
                    break;
                case 'steps':
                    initStepsPage();
                    break;
                case 'login':
                    initLoginPage();
                    break;
                case 'question':
                    console.log('🎯 Запускаем initQuestionPage...');
                    initQuestionPage();
                    break;
                case 'loading':
                    initLoadingPage();
                    break;
                case 'answers':
                    initAnswersPage();
                    break;
                case 'price':
                    initPricePage();
                    break;
                case 'payment':
                    initPaymentPage();
                    break;
                case 'download':
                    initDownloadPage();
                    break;
            }
        } else {
            console.log('⏳ TelegramWebApp not ready, retrying...');
            setTimeout(initTelegramApp, 100);
        }
    }
    
    // Вспомогательные функции для безопасной работы с Telegram API
    function safeMainButton(action, ...args) {
        try {
            if (window.TelegramWebApp && window.TelegramWebApp.MainButton) {
                return window.TelegramWebApp.MainButton[action](...args);
            } else {
                console.log(`❌ MainButton.${action} не поддерживается`);
                return false;
            }
        } catch (error) {
            console.error(`❌ Ошибка MainButton.${action}:`, error);
            return false;
        }
    }
    
    function safeBackButton(action, ...args) {
        try {
            if (window.TelegramWebApp && window.TelegramWebApp.BackButton) {
                return window.TelegramWebApp.BackButton[action](...args);
            } else {
                console.log(`❌ BackButton.${action} не поддерживается`);
                return false;
            }
        } catch (error) {
            console.error(`❌ Ошибка BackButton.${action}:`, error);
            return false;
        }
    }

    // Запуск инициализации
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTelegramApp);
    } else {
        initTelegramApp();
    }

    function getCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop().split('.')[0];
        return filename || 'index';
    }

    function initIndexPage() {
        // Развернуть viewport
        if (window.TelegramWebApp && window.TelegramWebApp.expandViewport) {
            window.TelegramWebApp.expandViewport();
        }
        
        // Скрыть стандартные кнопки
        safeMainButton('hide');
        safeBackButton('hide');

        // Обработка кнопки "Начать анализ"
        $('.button[href="steps.html"]').click(function(e) {
            e.preventDefault();
            window.TelegramWebApp.hapticFeedback('medium');
            window.location.href = 'steps.html';
        });
    }

    function initStepsPage() {
        // Показать кнопку назад (если поддерживается)
        try {
            if (window.TelegramWebApp.BackButton) {
                window.TelegramWebApp.BackButton.show();
            }
        } catch (error) {
            console.log('⬅️ BackButton не поддерживается:', error);
        }
        
        // Добавить обработчики для кнопок шагов
        $('.button').click(function() {
            window.TelegramWebApp.hapticFeedback('medium');
        });
    }

    function initLoginPage() {
        console.log('👤 =============================================================');
        console.log('👤 ИНИЦИАЛИЗАЦИЯ СТРАНИЦЫ ЛОГИНА');
        console.log('👤 =============================================================');
        
        // Показать кнопку назад (если поддерживается)
        safeBackButton('show');
        
        // Получить данные пользователя из Telegram
        const userData = window.TelegramWebApp.initDataUnsafe || {};
        const telegramId = window.TelegramWebApp.getUserId();
        
        console.log('👤 Telegram ID:', telegramId);
        console.log('👤 User Data:', userData);
        console.log('👤 window.TelegramWebApp доступен:', !!window.TelegramWebApp);
        console.log('👤 window.TelegramWebApp.getUserId доступен:', !!window.TelegramWebApp?.getUserId);
        
        // Асинхронная функция для загрузки профиля пользователя
        async function loadUserProfile() {
            try {
                console.log('Загружаем профиль пользователя...');
                console.log('URL запроса:', `/api/user/${telegramId}/profile`);
                
                const response = await fetch(`/api/user/${telegramId}/profile`);
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Профиль загружен:', result);
                    
                    // Заполняем поля, если данные есть в базе
                    if (result.user) {
                        if (result.user.name) {
                            $('#nameInput').val(result.user.name);
                        } else if (userData.user?.first_name) {
                            // Если имени нет в профиле, используем из Telegram
                            $('#nameInput').val(userData.user.first_name);
                        }
                        
                        if (result.user.age) {
                            $('#ageInput').val(result.user.age);
                        }
                        
                        if (result.user.gender) {
                            $('#genderInput').val(result.user.gender);
                            
                            // Обновляем отображение выбранного пола
                            const genderText = result.user.gender === 'male' ? 'Мужской' : 'Женский';
                            $('.select-placeholder').text(genderText);
                        }
                        
                        // Проверяем заполненность формы для показа кнопки
                        checkFormCompleteness();
                    }
                } else {
                    console.log('Профиль не найден или ошибка сервера:', response.status, response.statusText);
                    const errorText = await response.text();
                    console.log('Ответ сервера:', errorText);
                    
                    // Если профиль не найден, заполняем имя из Telegram
                    if (userData.user?.first_name) {
                        $('#nameInput').val(userData.user.first_name);
                    }
                }
            } catch (error) {
                console.error('Ошибка при загрузке профиля:', error);
                // В случае ошибки используем данные из Telegram
                if (userData.user?.first_name) {
                    $('#nameInput').val(userData.user.first_name);
                }
            }
        }
        
        // Загружаем профиль при инициализации страницы
        loadUserProfile();

        // Асинхронная функция для сохранения профиля
        async function saveProfile(name, age, gender) {
            try {
                console.log('Отправляем данные:', { name, age, gender, telegramId });
                
                const response = await fetch(`/api/user/${telegramId}/profile`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: name,
                        age: parseInt(age),
                        gender: gender
                    })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Ошибка сервера:', errorText);
                    throw new Error(`Ошибка сохранения данных: ${response.status}`);
                }

                const result = await response.json();
                console.log('Профиль сохранен:', result);
                return true;
            } catch (error) {
                console.error('Ошибка при сохранении профиля:', error);
                if (window.TelegramWebApp && window.TelegramWebApp.showAlert) {
                    window.TelegramWebApp.showAlert('Ошибка сохранения данных. Попробуйте еще раз.');
                } else {
                    alert('Ошибка сохранения данных. Попробуйте еще раз.');
                }
                return false;
            }
        }

        // Регистрируем обработчик главной кнопки один раз
        let mainButtonHandlerRegistered = false;
        
        // Обработка кнопки "Продолжить" (как через Telegram кнопку, так и через HTML кнопку)
        async function handleContinue() {
            const name = $('#nameInput').val().trim();
            const age = $('#ageInput').val().trim();
            const gender = $('#genderInput').val();

            if (!name || !age || !gender) {
                window.TelegramWebApp.showAlert('Пожалуйста, заполните все поля');
                return;
            }

            if (age < 1 || age > 120) {
                window.TelegramWebApp.showAlert('Пожалуйста, введите корректный возраст');
                return;
            }

            // Показать индикатор загрузки
            safeMainButton('setText', 'Сохранение...');
            safeMainButton('show');
            
            // Сохранить данные в базу
            const saved = await saveProfile(name, age, gender);
            
            if (saved) {
                // Также сохранить в localStorage для совместимости
                localStorage.setItem('userProfile', JSON.stringify({
                    name: name,
                    age: age,
                    gender: gender,
                    telegramUser: userData
                }));

                window.location.href = 'question.html';
            } else {
                // Восстановить кнопку
                safeMainButton('setText', 'Продолжить');
                safeMainButton('show');
            }
        }

        // Регистрируем обработчик главной кнопки один раз
        if (!mainButtonHandlerRegistered) {
            try {
                if (window.TelegramWebApp && window.TelegramWebApp.onEvent) {
                    window.TelegramWebApp.onEvent('mainButtonClicked', handleContinue);
                    console.log('✅ MainButton обработчик зарегистрирован');
                } else if (window.TelegramWebApp && window.TelegramWebApp.MainButton && window.TelegramWebApp.MainButton.onClick) {
                    window.TelegramWebApp.MainButton.onClick(handleContinue);
                    console.log('✅ MainButton onClick обработчик зарегистрирован');
                } else {
                    console.log('❌ MainButton обработчики не поддерживаются');
                }
                mainButtonHandlerRegistered = true;
            } catch (error) {
                console.error('❌ Ошибка регистрации MainButton обработчика:', error);
            }
        }

        // Обработка HTML кнопки "Продолжить"
        $('#continueButton').off('click').on('click', function(e) {
            e.preventDefault();
            handleContinue();
        });

        // Функция проверки заполненности формы
        function checkFormCompleteness() {
            const name = $('#nameInput').val().trim();
            const age = $('#ageInput').val().trim();
            const gender = $('#genderInput').val();
            
            if (name && age && gender) {
                safeMainButton('setText', 'Продолжить');
                safeMainButton('show');
            } else {
                safeMainButton('hide');
            }
        }

        // Проверка заполненности формы при изменении полей
        $('#nameInput, #ageInput, #genderInput').on('input change', checkFormCompleteness);
    }

    function initQuestionPage() {
        console.log('🎯 =============================================================');
        console.log('🎯 ИНИЦИАЛИЗАЦИЯ СТРАНИЦЫ ВОПРОСОВ');
        console.log('🎯 =============================================================');
        
        // Показать кнопку назад (если поддерживается)
        console.log('⬅️ Пытаемся показать BackButton');
        safeBackButton('show');
        
        // Переменные для работы с API
        let currentTelegramId = null;
        let currentQuestionData = null;
        const API_BASE_URL = window.location.origin;
        console.log('🌐 API_BASE_URL установлен в:', API_BASE_URL);
        
        // Получаем Telegram ID пользователя через унифицированный API
        function getTelegramUserId() {
            const userId = window.TelegramWebApp.getUserId();
            console.log('👤 getTelegramUserId() вернул:', userId);
            return userId;
        }
        
        // Загрузка текущего вопроса
        async function loadCurrentQuestion() {
            try {
                currentTelegramId = getTelegramUserId();
                console.log('📡 Loading question for user:', currentTelegramId);
                console.log('🌐 API_BASE_URL:', API_BASE_URL);
                
                if (!currentTelegramId) {
                    throw new Error('Не удалось получить Telegram ID пользователя');
                }
                
                const requestUrl = `${API_BASE_URL}/api/user/${currentTelegramId}/current-question`;
                console.log('📡 Request URL:', requestUrl);
                
                const response = await fetch(requestUrl);
                console.log('📡 Response status:', response.status);
                
                const data = await response.json();
                console.log('📡 Response data:', data);
                
                if (response.ok) {
                    currentQuestionData = data;
                    displayQuestion(data);
                    console.log('✅ Question loaded successfully');
                } else {
                    console.error('❌ Error loading question:', data.error);
                    $('#questionText').text('Ошибка загрузки вопроса: ' + (data.error || data.detail || 'неизвестная ошибка'));
                }
            } catch (error) {
                console.error('💥 Exception loading question:', error);
                $('#questionText').text('Ошибка загрузки вопроса: ' + error.message);
            }
        }
        
        // Отображение вопроса
        function displayQuestion(data) {
            const { question, progress, user } = data;
            
            $('#questionText').text(question.text);
            $('.current-question').text(progress.current);
            $('.question-count').text(progress.total);
            
            const textarea = $('#questionArea');
            textarea.val('');
            textarea.attr('maxlength', question.max_length || 1000);
            
            if (!user.is_paid && question.type === 'paid') {
                $('#questionText').append('<br><small style="color: #ff6b6b;">💎 Этот вопрос доступен в премиум-версии</small>');
            }
            
            console.log('Question loaded:', question);
        }
        
        // Отправка ответа
        async function submitAnswer() {
            const answerText = $('#questionArea').val().trim();
            
            if (!answerText) {
                window.TelegramWebApp.showAlert('Пожалуйста, введите ответ на вопрос');
                return;
            }
            
            if (!currentTelegramId) {
                window.TelegramWebApp.showAlert('Ошибка: не удалось получить ID пользователя');
                return;
            }
            
            // Тактильная обратная связь
            window.TelegramWebApp.hapticFeedback('medium');
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/user/${currentTelegramId}/answer`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text_answer: answerText,
                        answer_type: 'text'
                    })
                });
                
                const responseText = await response.text();
                let data;
                try {
                    data = JSON.parse(responseText);
                } catch (e) {
                    throw new Error('Сервер вернул некорректный JSON: ' + responseText);
                }
                
                if (response.ok) {
                    window.TelegramWebApp.hapticFeedback('light');
                    
                    if (data.status === 'next_question') {
                        currentQuestionData = {
                            question: data.next_question,
                            progress: data.progress,
                            user: currentQuestionData.user
                        };
                        
                        displayQuestion(currentQuestionData);
                        $('#questionArea').val('');
                        showSuccessMessage('Ответ сохранен!');
                        
                    } else if (data.status === 'test_completed') {
                        const message = data.message || 'Тест завершен!';
                        window.TelegramWebApp.showAlert(message);
                        setTimeout(() => {
                            window.location.href = 'download.html';
                        }, 1500);
                    }
                } else {
                    window.TelegramWebApp.handleError(data, 'Ошибка при сохранении ответа');
                }
            } catch (error) {
                window.TelegramWebApp.handleError(error, 'Ошибка при сохранении ответа');
            }
        }
        
        // Показать сообщение об успехе
        function showSuccessMessage(message) {
            const successDiv = $('<div>')
                .text(message)
                .css({
                    position: 'fixed',
                    top: '20px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: '#4CAF50',
                    color: 'white',
                    padding: '10px 20px',
                    borderRadius: '5px',
                    zIndex: 1000
                });
            
            $('body').append(successDiv);
            setTimeout(() => {
                successDiv.fadeOut(() => successDiv.remove());
            }, 2000);
        }
        
        // Настройка MainButton
        console.log('🔧 Настраиваем MainButton...');
        console.log('🔧 window.TelegramWebApp:', !!window.TelegramWebApp);
        console.log('🔧 window.TelegramWebApp.MainButton:', !!window.TelegramWebApp?.MainButton);
        
        try {
            if (window.TelegramWebApp && window.TelegramWebApp.MainButton) {
                window.TelegramWebApp.MainButton.setText('Следующий вопрос');
                window.TelegramWebApp.MainButton.show();
                window.TelegramWebApp.MainButton.onClick(submitAnswer);
                console.log('✅ MainButton настроена успешно');
            } else {
                console.log('❌ MainButton не доступна, используем HTML кнопку');
                // Fallback на HTML кнопку
                $('#nextButton').show().off('click').on('click', submitAnswer);
            }
        } catch (error) {
            console.error('❌ Ошибка настройки MainButton:', error);
            // Fallback на HTML кнопку
            $('#nextButton').show().off('click').on('click', submitAnswer);
        }
        
        // Обработка Enter в textarea
        $('#questionArea').on('keydown', function(e) {
            if (e.ctrlKey && e.keyCode === 13) {
                submitAnswer();
            }
        });
        
        // Обработка микрофона - транскрибация речи в текст  
        $('.micro-button').click(function() {
            window.TelegramWebApp.hapticFeedback('medium');
            startVoiceTranscription();
        });
        
        // Загружаем вопрос при инициализации
        console.log('🔄 Вызываем loadCurrentQuestion...');
        loadCurrentQuestion();
        
        // Для тестирования
        if (!localStorage.getItem('test_telegram_id')) {
            localStorage.setItem('test_telegram_id', '123456789');
            console.log('💾 Установлен тестовый ID: 123456789');
        }
        
        console.log('🎯 ============ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА ============');
        
        function startVoiceTranscription() {
            // Сначала пробуем использовать нативные возможности Telegram
            if (window.TelegramWebApp && window.TelegramWebApp.platform !== 'unknown') {
                // В Telegram всегда доступна клавиатура с микрофоном
                window.TelegramWebApp.showAlert('Используйте кнопку микрофона на клавиатуре Telegram для голосового ввода');
                
                // Фокусируемся на поле ввода, чтобы появилась клавиатура с микрофоном
                $('#questionArea').focus();
                
                // Добавляем подсказку в интерфейс
                showVoiceInputHint();
                return;
            }
            
            // Fallback: проверяем поддержку речевого ввода в браузере
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                window.TelegramWebApp.showAlert('Речевой ввод не поддерживается в данном браузере');
                return;
            }
            
            // Используем Web Speech API для транскрибации
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            // Настройки распознавания
            recognition.lang = 'ru-RU';
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;
            
            // Визуальная обратная связь
            $('.micro-button').addClass('recording');
            $('.micro-button img').attr('src', './images/pause-icon.svg');
            showTranscriptionIndicator();
            
            recognition.onstart = function() {
                console.log('Распознавание речи начато');
            };
            
            recognition.onresult = function(event) {
                let finalTranscript = '';
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                // Обновляем поле ввода
                const currentText = $('#questionArea').val();
                const newText = currentText + ' ' + finalTranscript;
                $('#questionArea').val(newText.trim());
                
                // Показываем промежуточный результат
                if (interimTranscript) {
                    updateTranscriptionIndicator('🎤 Слышу: ' + interimTranscript);
                }
            };
            
            recognition.onerror = function(event) {
                console.error('Ошибка распознавания речи:', event.error);
                stopTranscription();
                
                let errorMessage = 'Ошибка распознавания речи';
                switch(event.error) {
                    case 'network':
                        errorMessage = 'Ошибка сети. Проверьте подключение к интернету';
                        break;
                    case 'not-allowed':
                        errorMessage = 'Доступ к микрофону запрещен. Разрешите доступ в настройках браузера';
                        break;
                    case 'no-speech':
                        errorMessage = 'Речь не обнаружена. Попробуйте еще раз';
                        break;
                }
                
                window.TelegramWebApp.showAlert(errorMessage);
            };
            
            recognition.onend = function() {
                console.log('Распознавание речи завершено');
                stopTranscription();
            };
            
            // Запускаем распознавание
            try {
                recognition.start();
            } catch (error) {
                console.error('Ошибка запуска распознавания:', error);
                stopTranscription();
                window.TelegramWebApp.showAlert('Не удалось запустить распознавание речи');
            }
        }
        
        function stopTranscription() {
            // Восстанавливаем визуал
            $('.micro-button').removeClass('recording');
            $('.micro-button img').attr('src', './images/micro-icon.svg');
            hideTranscriptionIndicator();
        }
        
        function showTranscriptionIndicator() {
            const indicator = $('<div class="transcription-indicator">🎤 Говорите...</div>');
            indicator.css({
                position: 'fixed',
                top: '20px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: '#4CAF50',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '14px',
                fontWeight: 'bold',
                zIndex: 1000,
                animation: 'pulse 1s infinite'
            });
            
            $('body').append(indicator);
        }
        
        function updateTranscriptionIndicator(text) {
            $('.transcription-indicator').text(text);
        }
        
        function hideTranscriptionIndicator() {
            $('.transcription-indicator').remove();
        }
        
        function showVoiceInputHint() {
            const hint = $('<div class="voice-hint">🎤 Нажмите на микрофон на клавиатуре Telegram<br>📝 Ваша речь будет преобразована в текст</div>');
            hint.css({
                position: 'fixed',
                bottom: '120px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                padding: '12px 20px',
                borderRadius: '25px',
                fontSize: '14px',
                fontWeight: '500',
                zIndex: 1000,
                maxWidth: '320px',
                textAlign: 'center',
                lineHeight: '1.4',
                boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                border: '2px solid rgba(255,255,255,0.2)'
            });
            
            $('body').append(hint);
            
            // Убираем подсказку через 6 секунд
            setTimeout(() => {
                hint.fadeOut(1000, () => hint.remove());
            }, 6000);
            
            // Анимация появления
            hint.css('opacity', '0').animate({ opacity: 1 }, 500);
        }
    }

    function initLoadingPage() {
        // Скрыть все кнопки
        window.TelegramWebApp.MainButton.hide();
        window.TelegramWebApp.BackButton.hide();

        // Получаем Telegram ID и генерируем отчет
        const telegramId = window.TelegramWebApp.getUserId();

        // Проверяем статус пользователя и генерируем отчет
        async function checkUserStatusAndGenerateReport() {
            try {
                // Получаем информацию о пользователе
                const progressResponse = await fetch(`/api/user/${telegramId}/progress`);
                const progressData = await progressResponse.json();
                
                if (progressResponse.ok && progressData.user.test_completed) {
                    // Если тест завершен, переходим сразу к скачиванию
                    setTimeout(() => {
                        window.location.href = 'download.html';
                    }, 3000);
                } else {
                    // Если тест не завершен (недостаточно ответов), переходим к тарифам
                    setTimeout(() => {
                        window.location.href = 'price.html';
                    }, 3000);
                }
            } catch (error) {
                console.error('Error checking user status:', error);
                // В случае ошибки переходим к тарифам
                setTimeout(() => {
                    window.location.href = 'price.html';
                }, 3000);
            }
        }

        // Запускаем проверку
        checkUserStatusAndGenerateReport();
    }

    function initAnswersPage() {
        // Показать кнопку "Скачать отчет"
        window.TelegramWebApp.onEvent('mainButtonClicked', function() {
            window.location.href = 'download.html';
        });
        window.TelegramWebApp.MainButton.setText('Скачать отчет');
        window.TelegramWebApp.MainButton.show();
    }

    function initPricePage() {
        // Показать кнопку назад (если поддерживается)
        try {
            if (window.TelegramWebApp.BackButton) {
                window.TelegramWebApp.BackButton.show();
            }
        } catch (error) {
            console.log('⬅️ BackButton не поддерживается:', error);
        }

        // Получаем Telegram ID пользователя
        const telegramId = window.TelegramWebApp.getUserId();

        // Обработка выбора тарифа
        $('.price-plan-action .button').click(async function(e) {
            e.preventDefault();
            window.TelegramWebApp.hapticFeedback('medium');
            
            const planType = $(this).closest('.free-price-plan').length > 0 ? 'free' : 'paid';
            
            if (planType === 'free') {
                // Бесплатный план - проверяем количество ответов
                try {
                    const progressResponse = await fetch(`/api/user/${telegramId}/progress`);
                    const progressData = await progressResponse.json();
                    
                    if (progressResponse.ok) {
                        if (progressData.progress.answered >= 15) {
                            // Достаточно ответов для бесплатного отчета
                            window.location.href = 'download.html';
                        } else {
                            // Недостаточно ответов
                            window.TelegramWebApp.showAlert(`Для бесплатного отчета нужно ответить на все 15 вопросов. Вы ответили на ${progressData.progress.answered}.`);
                            setTimeout(() => {
                                window.location.href = 'question.html';
                            }, 2000);
                        }
                    } else {
                        window.TelegramWebApp.showAlert('Ошибка получения данных пользователя');
                    }
                } catch (error) {
                    console.error('Error checking user progress:', error);
                    window.TelegramWebApp.showAlert('Ошибка проверки прогресса');
                }
            } else {
                // Платный план - к оплате
                window.location.href = 'complete-payment.html';
            }
        });
    }

    function initPaymentPage() {
        // Показать кнопку назад (если поддерживается)
        try {
            if (window.TelegramWebApp.BackButton) {
                window.TelegramWebApp.BackButton.show();
            }
        } catch (error) {
            console.log('⬅️ BackButton не поддерживается:', error);
        }

        // Обработка успешной оплаты
        $('.button').click(function() {
            window.TelegramWebApp.hapticFeedback('light');
            window.location.href = 'answers.html';
        });
    }

    function initDownloadPage() {
        // Получаем Telegram ID пользователя
        const telegramId = window.TelegramWebApp.getUserId();

        // Показать кнопку "Завершить"
        window.TelegramWebApp.onEvent('mainButtonClicked', function() {
            // Закрыть приложение
            window.TelegramWebApp.close();
        });
        window.TelegramWebApp.MainButton.setText('Завершить');
        window.TelegramWebApp.MainButton.show();

        // Обработка скачивания отчета (УЛУЧШЕННАЯ ЛОГИКА для Telegram Web App)
        $('.button-download.telegram-download').click(async function() {
            window.TelegramWebApp.hapticFeedback('medium');
            
            console.log('🔽 Начинаем скачивание отчета...');
            console.log('📊 Telegram ID:', telegramId);
            console.log('🌐 Telegram Web App версия:', window.TelegramWebApp.version);
            
            const reportUrl = `${window.location.origin}/api/download/report/${telegramId}`;
            console.log('📁 URL отчета:', reportUrl);
            
            // Показываем индикатор загрузки
            const $button = $(this);
            const originalText = $button.find('span').text();
            $button.find('span').text('Скачиваем...');
            $button.prop('disabled', true);
            
            try {
                // НОВЫЙ МЕТОД: Скачивание через fetch + blob для реального сохранения файла
                console.log('📱 Используем оптимизированное скачивание для Telegram...');
                
                // Делаем запрос на получение файла
                const response = await fetch(reportUrl + '?download=1&source=telegram&t=' + Date.now());
                
                if (!response.ok) {
                    throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}`);
                }
                
                console.log('✅ Ответ получен, создаем blob...');
                
                // Создаем blob из ответа
                const blob = await response.blob();
                console.log('📄 Blob создан, размер:', blob.size, 'байт');
                
                // Проверяем, поддерживает ли Telegram Web App download API
                if (window.TelegramWebApp.downloadFile && 
                    window.TelegramWebApp.version && 
                    parseFloat(window.TelegramWebApp.version) >= 7.0) {
                    
                    console.log('📱 Пробуем нативный Telegram download API...');
                    
                    try {
                        // Создаем временный URL для blob
                        const blobUrl = window.URL.createObjectURL(blob);
                        
                        window.TelegramWebApp.downloadFile({
                            url: blobUrl,
                            file_name: `prizma-report-${telegramId}.pdf`
                        }, function(success) {
                            console.log('📱 Результат нативного API:', success);
                            window.URL.revokeObjectURL(blobUrl);
                            
                            if (success) {
                                window.TelegramWebApp.hapticFeedback('light');
                                window.TelegramWebApp.showAlert('✅ Отчет успешно скачан!\n\n📄 Найдите файл prizma-report-' + telegramId + '.pdf в загрузках вашего устройства.');
                            } else {
                                // Fallback к обычному методу
                                downloadViaBlob(blob);
                            }
                        });
                        
                        return; // Выходим, если нативный API запущен
                        
                    } catch (nativeError) {
                        console.error('📱 Ошибка нативного API:', nativeError);
                        // Продолжаем к fallback методу
                    }
                }
                
                // Fallback: обычное скачивание через blob и ссылку
                downloadViaBlob(blob);
                
                function downloadViaBlob(blob) {
                    console.log('🔗 Используем fallback скачивание через blob...');
                    
                    try {
                        // Создаем ссылку для скачивания
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `prizma-report-${telegramId}.pdf`;
                        a.style.display = 'none';
                        document.body.appendChild(a);
                        
                        console.log('⬇️ Инициируем скачивание...');
                        a.click();
                        
                        // Очистка
                        setTimeout(() => {
                            window.URL.revokeObjectURL(url);
                            if (a.parentNode) {
                                a.parentNode.removeChild(a);
                            }
                        }, 100);
                        
                        window.TelegramWebApp.hapticFeedback('light');
                        window.TelegramWebApp.showAlert('📁 Отчет скачан!\n\n' +
                            '💡 Найдите файл в загрузках вашего устройства:\n' +
                            '📄 prizma-report-' + telegramId + '.pdf\n\n' +
                            '❓ Если файл не появился, попробуйте:\n' +
                            '1. Проверить папку "Загрузки"\n' +
                            '2. Проверить уведомления о скачивании\n' +
                            '3. Открыть приложение через браузер');
                        
                        console.log('✅ Скачивание завершено через blob');
                        
                    } catch (blobError) {
                        console.error('🔗 Ошибка blob скачивания:', blobError);
                        
                        // Последний fallback - openLink
                        const directUrl = reportUrl + '?download=1&fallback=1&t=' + Date.now();
                        console.log('🌐 Последний fallback: openLink ->', directUrl);
                        
                        if (window.TelegramWebApp.openLink) {
                            window.TelegramWebApp.openLink(directUrl);
                            window.TelegramWebApp.showAlert('📁 Отчет открыт в браузере!\n\n' +
                                '💡 В открывшемся браузере нажмите кнопку "Скачать" или используйте меню "Сохранить как..."\n\n' +
                                '📄 Имя файла: prizma-report-' + telegramId + '.pdf');
                        } else {
                            throw new Error('Все методы скачивания недоступны');
                        }
                    }
                }
                
            } catch (error) {
                console.error('❌ Ошибка при скачивании отчета:', error);
                
                window.TelegramWebApp.showAlert('❌ Ошибка при скачивании отчета:\n\n' +
                    error.message + '\n\n' +
                    '💡 Попробуйте:\n' +
                    '1. Перезагрузить страницу\n' +
                    '2. Проверить интернет-соединение\n' +
                    '3. Открыть приложение в браузере\n' +
                    '4. Обратиться в поддержку');
            } finally {
                // Восстанавливаем кнопку
                setTimeout(() => {
                    $button.find('span').text(originalText);
                    $button.prop('disabled', false);
                }, 2000);
            }
            
            console.log('🔽 Завершили попытку скачивания отчета');
        });

        // Проверяем статус пользователя при загрузке страницы
        async function checkUserStatus() {
            try {
                const response = await fetch(`/api/user/${telegramId}/progress`);
                const data = await response.json();
                
                if (response.ok) {
                    // Обновляем информацию на странице если есть соответствующие элементы
                    if ($('.answers-count').length) {
                        $('.answers-count').text(data.progress.answered);
                    }
                    
                    if (!data.user.test_completed) {
                        // Если тест не завершен, показываем предупреждение
                        window.TelegramWebApp.showAlert('Внимание: тест не завершен полностью');
                    }
                }
            } catch (error) {
                console.error('Error checking user status:', error);
            }
        }
        
        checkUserStatus();
    }
}); 