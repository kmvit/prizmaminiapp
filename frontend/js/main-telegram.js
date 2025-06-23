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

    // Telegram Web App специфичный код
    if (window.TelegramWebApp) {
        
        // Инициализация для разных страниц
        const currentPage = getCurrentPage();
        console.log('Current page detected:', currentPage);
        console.log('Current URL:', window.location.href);
        
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
    }

    function getCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop().split('.')[0];
        return filename || 'index';
    }

    function initIndexPage() {
        // Развернуть viewport
        window.TelegramWebApp.expandViewport();
        
        // Скрыть стандартные кнопки
        window.TelegramWebApp.hideMainButton();
        window.TelegramWebApp.hideBackButton();

        // Обработка кнопки "Начать анализ"
        $('.button[href="steps.html"]').click(function(e) {
            e.preventDefault();
            window.TelegramWebApp.hapticFeedback('medium');
            window.location.href = 'steps.html';
        });
    }

    function initStepsPage() {
        // Показать кнопку назад
        window.TelegramWebApp.showBackButton();
        
        // Добавить обработчики для кнопок шагов
        $('.button').click(function() {
            window.TelegramWebApp.hapticFeedback('medium');
        });
    }

    function initLoginPage() {
        console.log('initLoginPage() called');
        // Показать кнопку назад
        window.TelegramWebApp.showBackButton();
        
        // Получить данные пользователя из Telegram
        const userData = window.TelegramWebApp.initDataUnsafe || {};
        const telegramId = userData.user?.id || 123456789; // Тестовый ID для отладки
        
        console.log('Telegram ID:', telegramId);
        console.log('User Data:', userData);
        
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
            if (window.TelegramWebApp && window.TelegramWebApp.showMainButton) {
                window.TelegramWebApp.showMainButton('Сохранение...');
            }
            
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
                if (window.TelegramWebApp && window.TelegramWebApp.showMainButton) {
                    window.TelegramWebApp.showMainButton('Продолжить', handleContinue);
                }
            }
        }

        // Показать главную кнопку для продолжения
        if (window.TelegramWebApp && window.TelegramWebApp.showMainButton) {
            window.TelegramWebApp.showMainButton('Продолжить', handleContinue);
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
                if (window.TelegramWebApp && window.TelegramWebApp.showMainButton) {
                    window.TelegramWebApp.showMainButton('Продолжить', handleContinue);
                }
            } else {
                if (window.TelegramWebApp && window.TelegramWebApp.hideMainButton) {
                    window.TelegramWebApp.hideMainButton();
                }
            }
        }

        // Проверка заполненности формы при изменении полей
        $('#nameInput, #ageInput, #genderInput').on('input change', checkFormCompleteness);
    }

    function initQuestionPage() {
        // Показать кнопку назад
        window.TelegramWebApp.showBackButton();
        
        const textarea = $('#questionArea');
        let currentTelegramId = null;
        let currentQuestionData = null;

        // Получаем Telegram ID пользователя
        function getTelegramUserId() {
            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
                return window.Telegram.WebApp.initDataUnsafe.user.id;
            }
            // Для тестирования - используем фиксированный ID
            const testId = localStorage.getItem('test_telegram_id');
            if (testId) {
                return parseInt(testId);
            }
            return 123456789;
        }

        // Загрузка текущего вопроса с сервера
        async function loadCurrentQuestion() {
            try {
                currentTelegramId = getTelegramUserId();
                console.log('Loading question for user:', currentTelegramId);
                
                if (!currentTelegramId) {
                    throw new Error('Не удалось получить Telegram ID пользователя');
                }
                
                const response = await fetch(`/api/user/${currentTelegramId}/current-question`);
                console.log('Response status:', response.status);
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if (response.ok) {
                    currentQuestionData = data;
                    displayQuestion(data);
                } else {
                    console.error('Error loading question:', data.error);
                    window.TelegramWebApp.showAlert('Ошибка загрузки вопроса: ' + (data.error || data.detail || 'неизвестная ошибка'));
                }
            } catch (error) {
                console.error('Error loading question:', error);
                window.TelegramWebApp.showAlert('Ошибка загрузки вопроса: ' + error.message);
            }
        }

        // Отображение вопроса
        function displayQuestion(data) {
            const { question, progress, user } = data;
            
            // Обновляем текст вопроса
            $('#questionText').text(question.text);
            
            // Обновляем счетчик вопросов
            $('.current-question').text(progress.current);
            $('.question-count').text(progress.total);
            
            // Настраиваем textarea
            textarea.val('');
            textarea.attr('maxlength', question.max_length || 1000);
            
            // Показываем информацию о типе аккаунта
            if (!user.is_paid && question.type === 'paid') {
                $('#questionText').append('<br><small style="color: #ff6b6b;">💎 Этот вопрос доступен в премиум-версии</small>');
            }
            
            console.log('Question loaded:', question);
        }

        // Отправка ответа на сервер
        async function submitAnswer() {
            const answerText = textarea.val().trim();
            
            if (!answerText) {
                window.TelegramWebApp.showAlert('Пожалуйста, введите ответ на вопрос');
                return;
            }
            
            if (!currentTelegramId) {
                window.TelegramWebApp.showAlert('Ошибка: не удалось получить ID пользователя');
                console.error('currentTelegramId is null/undefined');
                return;
            }
            
            // Показываем загрузку
            window.TelegramWebApp.hideMainButton();
            
            console.log('Отправляем ответ:', {
                telegramId: currentTelegramId,
                answer: answerText,
                questionId: currentQuestionData?.question?.id
            });
            
            try {
                const response = await fetch(`/api/user/${currentTelegramId}/answer`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text_answer: answerText,
                        answer_type: 'text'
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Тактильная обратная связь
                    window.TelegramWebApp.hapticFeedback('success');
                    
                    if (data.status === 'next_question') {
                        // Переходим к следующему вопросу
                        currentQuestionData = {
                            question: data.next_question,
                            progress: data.progress,
                            user: currentQuestionData.user
                        };
                        displayQuestion(currentQuestionData);
                        
                        // Очищаем textarea
                        textarea.val('');
                        
                    } else if (data.status === 'test_completed') {
                        // Тест завершен
                        window.TelegramWebApp.showAlert(data.message);
                        
                        // Для бесплатных пользователей переходим на загрузку, затем на скачивание
                        if (!currentQuestionData.user.is_paid) {
                            window.location.href = 'loading.html';
                        } else {
                            window.location.href = 'download.html';
                        }
                    }
                } else {
                    console.error('Error saving answer:', data.error);
                    window.TelegramWebApp.showAlert('Ошибка при сохранении ответа: ' + (data.error || data.detail));
                }
            } catch (error) {
                console.error('Error saving answer:', error);
                window.TelegramWebApp.showAlert('Ошибка при сохранении ответа');
            }
        }

        // Показать главную кнопку для отправки ответа
        function updateMainButton() {
            const hasText = textarea.val().trim().length > 0;
            if (hasText) {
                window.TelegramWebApp.showMainButton('Следующий вопрос', submitAnswer);
            } else {
                window.TelegramWebApp.hideMainButton();
            }
        }

        // Проверка наличия текста в области ввода
        textarea.on('input', updateMainButton);

        // Обработка микрофона - транскрибация речи в текст
        $('.micro-button').click(function() {
            window.TelegramWebApp.hapticFeedback('heavy');
            startVoiceTranscription();
        });

        // Загружаем первый вопрос при инициализации
        loadCurrentQuestion();
        
        // Для тестирования - сохраняем тестовый ID
        if (!localStorage.getItem('test_telegram_id')) {
            localStorage.setItem('test_telegram_id', '123456789');
        }
        
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
        window.TelegramWebApp.hideMainButton();
        window.TelegramWebApp.hideBackButton();

        // Получаем Telegram ID и генерируем отчет
        const telegramId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 
                          parseInt(localStorage.getItem('test_telegram_id')) || 
                          123456789;

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
        window.TelegramWebApp.showMainButton('Скачать отчет', function() {
            window.location.href = 'download.html';
        });
    }

    function initPricePage() {
        // Показать кнопку назад
        window.TelegramWebApp.showBackButton();

        // Получаем Telegram ID пользователя
        const telegramId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 
                          parseInt(localStorage.getItem('test_telegram_id')) || 
                          123456789;

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
        // Показать кнопку назад
        window.TelegramWebApp.showBackButton();

        // Обработка успешной оплаты
        $('.button').click(function() {
            window.TelegramWebApp.hapticFeedback('success');
            window.location.href = 'answers.html';
        });
    }

    function initDownloadPage() {
        // Получаем Telegram ID пользователя
        const telegramId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 
                          parseInt(localStorage.getItem('test_telegram_id')) || 
                          123456789;

        // Показать кнопку "Завершить"
        window.TelegramWebApp.showMainButton('Завершить', function() {
            // Закрыть приложение
            window.TelegramWebApp.close();
        });

        // Обработка скачивания отчета
        $('.button-download').click(async function() {
            window.TelegramWebApp.hapticFeedback('medium');
            
            try {
                // Скачиваем отчет через API
                const response = await fetch(`/api/download/report/${telegramId}`);
                
                if (response.ok) {
                    // Создаем blob из ответа
                    const blob = await response.blob();
                    
                    // Создаем ссылку для скачивания
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `prizma-report-${telegramId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    window.TelegramWebApp.hapticFeedback('success');
                } else {
                    const errorData = await response.json();
                    window.TelegramWebApp.showAlert('Ошибка при скачивании отчета: ' + (errorData.detail || 'неизвестная ошибка'));
                }
            } catch (error) {
                console.error('Error downloading report:', error);
                window.TelegramWebApp.showAlert('Ошибка при скачивании отчета');
            }
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