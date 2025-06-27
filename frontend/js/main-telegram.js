'use strict';
$(function() {
    // ========================================
    // УНИФИЦИРОВАННЫЕ УТИЛИТЫ (устраняют дублирование)
    // ========================================
    
    // Получение Telegram ID пользователя
    function getTelegramUserId() {
        // Приоритет 1: initDataUnsafe (более надежный)
        if (window.TelegramWebApp && window.TelegramWebApp.initDataUnsafe && window.TelegramWebApp.initDataUnsafe.user) {
            return window.TelegramWebApp.initDataUnsafe.user.id;
        }
        // Приоритет 2: getUserId() метод
        if (window.TelegramWebApp && window.TelegramWebApp.getUserId) {
            return window.TelegramWebApp.getUserId();
        }
        // Для тестирования - используем фиксированный ID
        const testId = localStorage.getItem('test_telegram_id');
        if (testId) {
            return parseInt(testId);
        }
        return 123456789;
    }

    // Проверка, работаем ли мы в Telegram Web App
    function isInTelegramWebApp() {
        return !!(window.Telegram && window.Telegram.WebApp) || 
               !!(window.TelegramWebApp && window.TelegramWebApp.tg) ||
               !!window.TelegramWebApp;
    }

    // Безопасная тактильная обратная связь
    function safeHapticFeedback(type = 'light') {
        try {
            if (isInTelegramWebApp()) {
                const api = getTelegramAPI();
                if (api && api.hapticFeedback) {
                    api.hapticFeedback(type);
                } else if (api && api.HapticFeedback && api.HapticFeedback.impactOccurred) {
                    api.HapticFeedback.impactOccurred(type);
                }
            }
        } catch (error) {
            console.log('⚠️ Не удалось вызвать тактильную обратную связь:', error);
        }
    }

    // Безопасное отображение алерта
    function safeShowAlert(message) {
        try {
            if (isInTelegramWebApp()) {
                const api = getTelegramAPI();
                if (api && api.showAlert) {
                    api.showAlert(message);
                    return;
                }
            }
            // Fallback для браузера
            alert(message);
        } catch (error) {
            console.error('❌ Ошибка отображения алерта:', error);
            alert(message);
        }
    }

    // Получение правильного Telegram API
    function getTelegramAPI() {
        if (window.Telegram && window.Telegram.WebApp) {
            return window.Telegram.WebApp;
        } else if (window.TelegramWebApp && window.TelegramWebApp.tg) {
            return window.TelegramWebApp.tg;
        } else if (window.TelegramWebApp) {
            return window.TelegramWebApp;
        }
        return null;
    }

    // API configuration
    const API_BASE_URL = window.location.origin;

    // ========================================
    // СУЩЕСТВУЮЩИЙ КОД ИЗ MAIN.JS
    // ========================================

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
        safeHapticFeedback('light');
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
        safeHapticFeedback('medium');
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

    // Запуск инициализации с защитой от двойного вызова
    let appInitialized = false;
    
    function safeInitTelegramApp() {
        if (appInitialized) {
            console.log('⚠️ TelegramApp уже инициализирован, пропускаем повторную инициализацию');
            return;
        }
        appInitialized = true;
        console.log('🚀 Инициализируем TelegramApp (первый раз)');
        initTelegramApp();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', safeInitTelegramApp);
    } else {
        safeInitTelegramApp();
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
            safeHapticFeedback('medium');
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
            safeHapticFeedback('medium');
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
                safeShowAlert('Ошибка сохранения данных. Попробуйте еще раз.');
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
                safeShowAlert('Пожалуйста, заполните все поля');
                return;
            }

            if (age < 1 || age > 120) {
                safeShowAlert('Пожалуйста, введите корректный возраст');
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
        console.log('🌐 API_BASE_URL установлен в:', API_BASE_URL);
        
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
                safeShowAlert('Пожалуйста, введите ответ на вопрос');
                return;
            }
            
            if (!currentTelegramId) {
                safeShowAlert('Ошибка: не удалось получить ID пользователя');
                return;
            }
            
            // Тактильная обратная связь
            safeHapticFeedback('medium');
            
            try {
                console.log('📤 Отправляем ответ на сервер...');
                const response = await fetch(`${API_BASE_URL}/api/user/${currentTelegramId}/answer`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text_answer: answerText,
                        answer_type: 'text'
                    })
                });
                
                console.log('📥 Получен ответ сервера:', response.status, response.statusText);
                const responseText = await response.text();
                console.log('📄 Текст ответа:', responseText);
                
                let data;
                try {
                    data = JSON.parse(responseText);
                } catch (e) {
                    console.error('❌ Ошибка парсинга JSON:', e);
                    console.error('❌ Полученный текст:', responseText);
                    throw new Error('Сервер вернул некорректный JSON: ' + responseText);
                }
                
                if (response.ok) {
                    safeHapticFeedback('light');
                    
                    console.log('✅ Ответ сервера получен:', data);
                    
                    if (data.status === 'next_question') {
                        console.log('➡️ Переход к следующему вопросу:', data.next_question.order_number);
                        currentQuestionData = {
                            question: data.next_question,
                            progress: data.progress,
                            user: currentQuestionData.user
                        };
                        
                        displayQuestion(currentQuestionData);
                        $('#questionArea').val('');
                        showSuccessMessage('Ответ сохранен!');
                        
                    } else if (data.status === 'test_completed') {
                        console.log('🎉 Тест завершен! Перенаправляем на loading.html для генерации отчета');
                        const message = data.message || 'Тест завершен!';
                        safeShowAlert(message);
                        setTimeout(() => {
                            window.location.href = 'loading.html';
                        }, 1500);
                        
                    } else {
                        console.warn('⚠️ Неизвестный статус ответа:', data.status);
                    }
                } else {
                    console.error('❌ Ошибка ответа сервера:', response.status, data);
                    safeShowAlert('Ошибка при сохранении ответа');
                }
            } catch (error) {
                safeShowAlert('Ошибка при сохранении ответа');
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
        
        // Скрыть Telegram MainButton и использовать только HTML кнопку
        console.log('🔧 Отключаем MainButton и используем HTML кнопку...');
        
        try {
            if (window.TelegramWebApp && window.TelegramWebApp.MainButton) {
                window.TelegramWebApp.MainButton.hide();
                console.log('✅ MainButton скрыта');
            }
        } catch (error) {
            console.error('❌ Ошибка скрытия MainButton:', error);
        }
        
        // Используем только HTML кнопку с SVG треугольником
        $('#nextButton').show().off('click').on('click', submitAnswer);
        console.log('✅ HTML кнопка активирована');
        
        // Обработка Enter в textarea
        $('#questionArea').on('keydown', function(e) {
            if (e.ctrlKey && e.keyCode === 13) {
                submitAnswer();
            }
        });
        
        // Обработка микрофона - транскрибация речи в текст  
        $('.micro-button').click(function() {
            safeHapticFeedback('medium');
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
                safeShowAlert('Используйте кнопку микрофона на Вашей клавиатуре для голосового ввода');
                
                // Фокусируемся на поле ввода, чтобы появилась клавиатура с микрофоном
                $('#questionArea').focus();
                
                // Добавляем подсказку в интерфейс
                showVoiceInputHint();
                return;
            }
            
            // Fallback: проверяем поддержку речевого ввода в браузере
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                safeShowAlert('Речевой ввод не поддерживается в данном браузере');
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
                
                safeShowAlert(errorMessage);
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
                safeShowAlert('Не удалось запустить распознавание речи');
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
        console.log('⏳ Инициализация страницы загрузки...');
        
        // Скрыть все кнопки
        safeMainButton('hide');
        safeBackButton('hide');

        // Получаем Telegram ID
        const telegramId = getTelegramUserId();
        
        if (!telegramId) {
            console.error('❌ Не удалось получить Telegram ID');
            safeShowAlert('Ошибка: не удалось получить ID пользователя');
            window.location.href = 'index.html';
            return;
        }

        console.log('👤 Telegram ID:', telegramId);

        // Функция для обновления статуса на странице
        function updateLoadingStatus(message) {
            const statusElement = document.getElementById('loading-status');
            if (statusElement) {
                statusElement.textContent = message;
            }
        }

        // Проверяем статус генерации отчета каждые 2 секунды
        async function checkReportStatus() {
            try {
                console.log('🔍 Проверяем статус генерации отчета...');
                const response = await fetch(`/api/user/${telegramId}/report-status`);
                const data = await response.json();
                
                console.log('📊 Статус отчета:', data);
                
                if (data.status === 'ready') {
                    console.log('✅ Отчет готов! Перенаправляем на download.html');
                    updateLoadingStatus('Отчет готов! Переходим к скачиванию...');
                    safeHapticFeedback('light');
                    setTimeout(() => {
                        window.location.href = 'download.html';
                    }, 1000);
                    return true; // Останавливаем проверку
                    
                } else if (data.status === 'generating') {
                    console.log('⏳ Отчет генерируется, ждем...');
                    updateLoadingStatus('Создаем персональный анализ...');
                    return false; // Продолжаем проверку
                    
                } else if (data.status === 'test_not_completed') {
                    console.log('⚠️ Тест не завершен, перенаправляем на price.html');
                    updateLoadingStatus('Тест не завершен...');
                    setTimeout(() => {
                        window.location.href = 'price.html';
                    }, 2000);
                    return true; // Останавливаем проверку
                    
                } else if (data.status === 'error') {
                    console.error('❌ Ошибка генерации отчета:', data.message);
                    updateLoadingStatus('Ошибка генерации. Попробуем позже...');
                    safeShowAlert('Ошибка при генерации отчета. Попробуйте позже.');
                    setTimeout(() => {
                        window.location.href = 'download.html'; // Все равно переходим на скачивание
                    }, 3000);
                    return true; // Останавливаем проверку
                }
                
            } catch (error) {
                console.error('❌ Ошибка проверки статуса отчета:', error);
                updateLoadingStatus('Проблема с подключением...');
                // После ошибки переходим на download.html
                setTimeout(() => {
                    window.location.href = 'download.html';
                }, 3000);
                return true; // Останавливаем проверку
            }
            
            return false; // Продолжаем проверку
        }

        // Запускаем первую проверку
        checkReportStatus().then(shouldStop => {
            if (!shouldStop) {
                // Если отчет еще генерируется, проверяем каждые 2 секунды
                const checkInterval = setInterval(async () => {
                    const shouldStop = await checkReportStatus();
                    if (shouldStop) {
                        clearInterval(checkInterval);
                    }
                }, 2000);
                
                // Максимальное время ожидания - 60 секунд
                setTimeout(() => {
                    clearInterval(checkInterval);
                    console.log('⏰ Превышен лимит времени ожидания, переходим на download.html');
                    window.location.href = 'download.html';
                }, 60000);
            }
        });
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
            safeHapticFeedback('medium');
            
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
                            safeShowAlert(`Для бесплатного отчета нужно ответить на все 10 вопросов. Вы ответили на ${progressData.progress.answered}.`);
                            setTimeout(() => {
                                window.location.href = 'question.html';
                            }, 2000);
                        }
                    } else {
                        safeShowAlert('Ошибка получения данных пользователя');
                    }
                } catch (error) {
                    console.error('Error checking user progress:', error);
                    safeShowAlert('Ошибка проверки прогресса');
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
            safeHapticFeedback('light');
            window.location.href = 'answers.html';
        });
    }

    function initDownloadPage() {
        console.log('📁 Инициализация страницы скачивания...');
        
        // Проверяем, была ли уже инициализирована эта страница
        if (window.downloadPageInitialized) {
            console.log('⚠️ Страница скачивания уже инициализирована, пропускаем');
            return;
        }
        window.downloadPageInitialized = true;
        
        // Флаг для предотвращения повторных вызовов
        let isDownloading = false;

        // Универсальное скачивание отчета (умный выбор метода)
        async function downloadPersonalReport(fallback = false) {
            // Защита от повторных вызовов
            if (isDownloading) {
                console.log('⚠️ Скачивание уже в процессе, игнорируем повторный вызов');
                return;
            }
            
            const telegramId = getTelegramUserId();
            
            if (!telegramId) {
                const alertMsg = 'Ошибка: не удалось получить ID пользователя';
                safeShowAlert(alertMsg);
                return;
            }
            
            isDownloading = true;
            
            console.log('📁 Начинаем скачивание отчета для пользователя:', telegramId);
            console.log('🔧 Fallback режим:', fallback);
            console.log('📱 В Telegram Web App:', isInTelegramWebApp());
            
            const $button = fallback ? $('#downloadReportFallback') : $('#downloadReport');
            const $span = $button.find('.download-file-text span');
            const originalText = $span.text();
            
            try {
                // Показываем индикатор загрузки
                $button.addClass('loading');
                $span.text('Генерируем отчет...');
                
                // Тактильная обратная связь для Telegram
                safeHapticFeedback('medium');
                
                const reportUrl = `${API_BASE_URL}/api/download/report/${telegramId}`;
                
                if (isInTelegramWebApp() && !fallback) {
                    // В Telegram Web App используем простую и надежную логику
                    console.log('📱 Используем Telegram Web App API...');
                    
                    // Простой метод: openLink
                    console.log('🔗 Используем Telegram openLink...');
                    const downloadUrl = reportUrl + '?download=1&source=telegram&t=' + Date.now();
                    
                    // Используем правильный API в зависимости от доступности
                    const telegramAPI = getTelegramAPI();
                    
                    if (telegramAPI && telegramAPI.openLink) {
                        console.log('🔗 Открываем через Telegram openLink:', downloadUrl);
                        telegramAPI.openLink(downloadUrl);
                        
                        $span.text('Отчет открыт!');
                        
                        // Тактильная обратная связь
                        safeHapticFeedback('light');
                        
                        if (telegramAPI.showAlert) {
                            telegramAPI.showAlert('📁 Отчет открыт в браузере!\n\n' +
                                '💡 Браузер должен автоматически скачать файл.\n' +
                                'Если этого не произошло - проверьте папку "Загрузки".\n\n' +
                                '📄 Имя файла: prizma-report-' + telegramId + '.pdf');
                        }
                        
                        // Показываем альтернативные кнопки через 3 секунды
                        setTimeout(() => {
                            $('#downloadReportFallback').fadeIn();
                            setTimeout(() => {
                                $('#downloadReportDirect').fadeIn();
                            }, 2000);
                        }, 3000);
                        
                        // ПРИНУДИТЕЛЬНО завершаем выполнение функции
                        console.log('✅ Telegram openLink выполнен, завершаем функцию');
                        return; // ВАЖНО: выходим из функции после успешного вызова
                    } else {
                        console.log('⚠️ openLink недоступен, переходим к fallback методу');
                        // НЕ выбрасываем ошибку, просто продолжаем к fallback
                    }
                }
                
                // Fallback метод: обычное скачивание через fetch + blob
                console.log('🌐 Используем обычное скачивание через fetch...');
                
                $span.text('Скачиваем файл...');
                
                const fetchUrl = reportUrl + (fallback ? '?download=1&method=fallback' : '?download=1&method=fetch') + '&t=' + Date.now();
                const response = await fetch(fetchUrl);
                
                if (response.ok) {
                    console.log('✅ Ответ получен, создаем blob...');
                    
                    // Создаем blob из ответа
                    const blob = await response.blob();
                    console.log('📄 Blob создан, размер:', blob.size, 'байт');
                    
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
                    
                    // Успешное завершение
                    $span.text('Отчет скачан!');
                    
                    safeHapticFeedback('light');
                    
                    console.log('✅ Скачивание завершено успешно');
                    
                } else {
                    const errorData = await response.json();
                    const errorMsg = 'Ошибка при скачивании: ' + (errorData.detail || 'Неизвестная ошибка');
                    
                    console.error('❌ Ошибка сервера:', errorData);
                    
                    safeShowAlert(errorMsg);
                    
                    // Показываем альтернативные кнопки при ошибке
                    if (!fallback) {
                        $('#downloadReportFallback').fadeIn();
                        setTimeout(() => {
                            $('#downloadReportDirect').fadeIn();
                        }, 1000);
                    }
                }
                
            } catch (error) {
                console.error('❌ Ошибка при скачивании отчета:', error);
                
                const errorMsg = 'Ошибка при скачивании отчета: ' + error.message;
                
                safeShowAlert(errorMsg + '\n\nПопробуйте альтернативное скачивание или обновите страницу.');
                
                // Показываем альтернативные кнопки при ошибке
                if (!fallback) {
                    $('#downloadReportFallback').fadeIn();
                    setTimeout(() => {
                        $('#downloadReportDirect').fadeIn();
                    }, 1000);
                }
                
            } finally {
                // Восстанавливаем кнопку
                $button.removeClass('loading');
                setTimeout(() => {
                    $span.text(originalText);
                }, 2000);
                
                // Сбрасываем флаг через небольшую задержку чтобы избежать случайных повторных кликов
                setTimeout(() => {
                    isDownloading = false;
                }, 1000);
            }
        }

        // Привязываем обработчики к кнопкам скачивания
        function setupDownloadHandlers() {
            // ОЧИЩАЕМ старые обработчики чтобы избежать дублирования
            $('#downloadReport').off('click');
            $('#downloadReportFallback').off('click');
            $('#downloadReportDirect').off('click');
            
            // Основная кнопка скачивания
            $('#downloadReport').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // Останавливаем всплытие события
                e.stopImmediatePropagation(); // Останавливаем все обработчики
                
                if (isDownloading) {
                    console.log('⚠️ Клик проигнорирован - скачивание уже в процессе');
                    return false;
                }
                
                console.log('🖱️ Клик по основной кнопке скачивания');
                downloadPersonalReport(false); // Основной метод
                return false;
            });
            
            // Альтернативная кнопка скачивания
            $('#downloadReportFallback').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // Останавливаем всплытие события
                e.stopImmediatePropagation(); // Останавливаем все обработчики
                
                if (isDownloading) {
                    console.log('⚠️ Клик проигнорирован - скачивание уже в процессе');
                    return false;
                }
                
                console.log('🖱️ Клик по альтернативной кнопке скачивания');
                downloadPersonalReport(true); // Fallback метод
                return false;
            });
            
            // Прямая ссылка для крайних случаев
            $('#downloadReportDirect').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                const telegramId = getTelegramUserId();
                const directUrl = `${API_BASE_URL}/api/download/report/${telegramId}?download=1&direct=1&t=${Date.now()}`;
                
                console.log('🖱️ Клик по прямой ссылке скачивания');
                
                // Используем правильный API
                const telegramAPI = getTelegramAPI();
                
                if (isInTelegramWebApp() && telegramAPI && telegramAPI.openLink) {
                    telegramAPI.openLink(directUrl);
                    if (telegramAPI.showAlert) {
                        telegramAPI.showAlert('📁 Файл открыт в браузере!\n\nИспользуйте меню браузера "Сохранить как..." для скачивания файла.');
                    }
                } else {
                    window.open(directUrl, '_blank');
                }
            });
        }

        // Проверка статуса пользователя при загрузке
        async function checkUserStatusOnLoad() {
            const telegramId = getTelegramUserId();
            
            if (!telegramId) return;
            
            try {
                console.log('🔍 Проверяем статус пользователя при загрузке...');
                const response = await fetch(`${API_BASE_URL}/api/user/${telegramId}/progress`);
                const data = await response.json();
                
                if (response.ok) {
                    console.log('📊 Данные пользователя:', data);
                    
                    if (!data.user.test_completed) {
                        console.log('⚠️ Тест не завершен, перенаправляем...');
                        
                        safeShowAlert('⚠️ Тест не завершен!\n\nВернитесь к прохождению теста для получения отчета.');
                        setTimeout(() => {
                            window.location.href = 'question.html';
                        }, 2000);
                    } else {
                        console.log('✅ Тест завершен, отчет доступен');
                        
                        // Обновляем информацию на странице если есть соответствующие элементы
                        if ($('.answers-count').length) {
                            $('.answers-count').text(data.progress.answered);
                        }
                    }
                } else {
                    console.error('❌ Ошибка получения статуса:', data);
                }
            } catch (error) {
                console.error('❌ Ошибка проверки статуса пользователя:', error);
            }
        }

        // Показать кнопку "Завершить"
        try {
            if (window.TelegramWebApp.MainButton) {
                window.TelegramWebApp.MainButton.onClick(function() {
                    // Закрыть приложение
                    window.TelegramWebApp.close();
                });
                window.TelegramWebApp.MainButton.setText('Завершить');
                window.TelegramWebApp.MainButton.show();
            }
        } catch (error) {
            console.log('❌ MainButton не поддерживается:', error);
        }

        // Инициализация обработчиков и проверки
        setupDownloadHandlers();
        checkUserStatusOnLoad();
        
        // Для тестирования - сохраняем тестовый ID
        if (!localStorage.getItem('test_telegram_id')) {
            localStorage.setItem('test_telegram_id', '123456789');
        }
        
        console.log('📁 Страница скачивания инициализирована');
    }
}); 