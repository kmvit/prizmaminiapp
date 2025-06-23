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
        let currentQuestion = 1;
        const totalQuestions = 10; // Настроить по необходимости

        // Обновление номера вопроса
        $('.question-num span').text(`${currentQuestion}/${totalQuestions}`);

        // Показать главную кнопку для отправки ответа
        window.TelegramWebApp.showMainButton('Следующий вопрос', function() {
            const answer = textarea.val().trim();
            
            if (!answer) {
                window.TelegramWebApp.showAlert('Пожалуйста, ответьте на вопрос');
                return;
            }

            // Сохранить ответ
            let answers = JSON.parse(localStorage.getItem('userAnswers') || '[]');
            answers.push({
                question: currentQuestion,
                answer: answer,
                timestamp: new Date().toISOString()
            });
            localStorage.setItem('userAnswers', JSON.stringify(answers));

            // Переход к следующему вопросу или завершение
            if (currentQuestion < totalQuestions) {
                currentQuestion++;
                $('.question-num span').text(`${currentQuestion}/${totalQuestions}`);
                textarea.val('');
                window.TelegramWebApp.hideMainButton();
            } else {
                // Завершение опроса
                window.location.href = 'loading.html';
            }
        });

        // Проверка наличия текста в области ввода
        textarea.on('input', function() {
            const hasText = $(this).val().trim().length > 0;
            if (hasText) {
                window.TelegramWebApp.showMainButton('Следующий вопрос');
            } else {
                window.TelegramWebApp.hideMainButton();
            }
        });

        // Обработка микрофона (если есть)
        $('.micro-button').click(function() {
            window.TelegramWebApp.hapticFeedback('heavy');
            // Здесь будет логика записи голоса
        });
    }

    function initLoadingPage() {
        // Скрыть все кнопки
        window.TelegramWebApp.hideMainButton();
        window.TelegramWebApp.hideBackButton();

        // Симуляция обработки данных
        setTimeout(function() {
            window.location.href = 'price.html';
        }, 5000); // 5 секунд загрузки
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

        // Обработка выбора тарифа
        $('.price-plan-action .button').click(function(e) {
            e.preventDefault();
            window.TelegramWebApp.hapticFeedback('medium');
            
            const planType = $(this).closest('.free-price-plan').length > 0 ? 'free' : 'paid';
            
            if (planType === 'free') {
                // Бесплатный план - сразу к результатам
                window.location.href = 'answers.html';
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
        // Показать кнопку "Завершить"
        window.TelegramWebApp.showMainButton('Завершить', function() {
            // Отправить данные в бота и закрыть приложение
            const userData = {
                profile: JSON.parse(localStorage.getItem('userProfile') || '{}'),
                answers: JSON.parse(localStorage.getItem('userAnswers') || '[]'),
                completed: true,
                timestamp: new Date().toISOString()
            };
            
            window.TelegramWebApp.sendData(userData);
        });

        // Обработка скачивания
        $('.button-download').click(function() {
            window.TelegramWebApp.hapticFeedback('medium');
            // Логика скачивания файла
        });
    }
}); 