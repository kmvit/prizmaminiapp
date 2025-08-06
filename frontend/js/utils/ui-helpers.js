/**
 * UI Helpers - Утилиты для пользовательского интерфейса
 * Вспомогательные функции для работы с UI элементами
 */

class UIHelpers {
    /**
     * Настройка выпадающего списка
     * @param {string} selectId - ID элемента select
     */
    static setupSelectDropdown(selectId = 'selectOptions') {
        const selectContainer = document.querySelector('.custom-select');
        if (!selectContainer) return;

        const selected = selectContainer.querySelector('.select-selected');
        const options = selectContainer.querySelector('.select-options');
        const hiddenInput = selectContainer.querySelector('input[type="hidden"]');

        // Показать/скрыть опции при клике
        selected.addEventListener('click', function(e) {
            e.stopPropagation();
            options.classList.toggle('show');
        });

        // Обработка выбора опции
        options.addEventListener('click', function(e) {
            if (e.target.classList.contains('option')) {
                const value = e.target.getAttribute('data-value');
                const text = e.target.textContent;
                
                // Обновить отображение
                selected.querySelector('.select-placeholder').textContent = text;
                hiddenInput.value = value;
                
                // Скрыть опции
                options.classList.remove('show');
                
                // Тактильная обратная связь
                if (window.TelegramWebApp) {
                    window.TelegramWebApp.hapticFeedback('light');
                }
            }
        });

        // Скрыть при клике вне элемента
        document.addEventListener('click', function() {
            options.classList.remove('show');
        });
    }

    /**
     * Настройка аккордеона
     * @param {string} selector - Селектор элементов аккордеона
     */
    static setupAccordion(selector = '.accordion-item') {
        const accordionItems = document.querySelectorAll(selector);
        
        accordionItems.forEach(item => {
            const header = item.querySelector('.accordion-header');
            const content = item.querySelector('.accordion-content');
            
            if (header && content) {
                header.addEventListener('click', function() {
                    const isActive = item.classList.contains('active');
                    
                    // Закрыть все элементы
                    accordionItems.forEach(otherItem => {
                        otherItem.classList.remove('active');
                        const otherContent = otherItem.querySelector('.accordion-content');
                        if (otherContent) {
                            otherContent.style.maxHeight = null;
                        }
                    });
                    
                    // Открыть текущий элемент если он был закрыт
                    if (!isActive) {
                        item.classList.add('active');
                        content.style.maxHeight = content.scrollHeight + 'px';
                        
                        // Тактильная обратная связь
                        if (window.TelegramWebApp) {
                            window.TelegramWebApp.hapticFeedback('light');
                        }
                    }
                });
            }
        });
    }

    /**
     * Настройка фокуса на textarea
     * @param {string} textareaId - ID textarea элемента
     */
    static setupTextareaFocus(textareaId = 'questionArea') {
        const textarea = document.getElementById(textareaId);
        if (!textarea) return;

        // Автофокус при загрузке страницы
        textarea.focus();

        // Автоматическое изменение размера
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });

        // Обработка Enter для отправки
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const nextButton = document.getElementById('nextButton');
                if (nextButton) {
                    nextButton.click();
                }
            }
        });
    }

    /**
     * Показать сообщение об успехе
     * @param {string} message - Текст сообщения
     * @param {number} duration - Длительность показа в мс
     */
    static showSuccessMessage(message, duration = 3000) {
        // Создать элемент сообщения
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 1000;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
        `;

        // Добавить стили анимации
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
                to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Добавить на страницу
        document.body.appendChild(successDiv);

        // Удалить через указанное время
        setTimeout(() => {
            successDiv.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (successDiv.parentNode) {
                    successDiv.parentNode.removeChild(successDiv);
                }
            }, 300);
        }, duration);
    }

    /**
     * Показать индикатор загрузки
     * @param {string} message - Сообщение загрузки
     */
    static showLoadingIndicator(message = 'Загрузка...') {
        // Создать элемент загрузки
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="loading-overlay">
                <div class="loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                </div>
                <div class="loading-text">${message}</div>
            </div>
        `;
        loadingDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        // Добавить стили для спиннера
        const style = document.createElement('style');
        style.textContent = `
            .loading-spinner {
                display: inline-block;
                position: relative;
                width: 80px;
                height: 80px;
            }
            .spinner-ring {
                box-sizing: border-box;
                display: block;
                position: absolute;
                width: 64px;
                height: 64px;
                margin: 8px;
                border: 8px solid #fff;
                border-radius: 50%;
                animation: spinner-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
                border-color: #fff transparent transparent transparent;
            }
            .spinner-ring:nth-child(1) { animation-delay: -0.45s; }
            .spinner-ring:nth-child(2) { animation-delay: -0.3s; }
            .spinner-ring:nth-child(3) { animation-delay: -0.15s; }
            @keyframes spinner-ring {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .loading-text {
                color: white;
                margin-top: 16px;
                font-size: 16px;
                text-align: center;
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(loadingDiv);
    }

    /**
     * Скрыть индикатор загрузки
     */
    static hideLoadingIndicator() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    /**
     * Обновить состояние кнопки
     * @param {HTMLElement} button - Элемент кнопки
     * @param {boolean} enabled - Включена ли кнопка
     * @param {string} text - Текст кнопки
     */
    static updateButtonState(button, enabled, text) {
        if (!button) return;

        button.disabled = !enabled;
        if (text) {
            button.textContent = text;
        }

        if (enabled) {
            button.classList.remove('disabled');
            button.style.opacity = '1';
        } else {
            button.classList.add('disabled');
            button.style.opacity = '0.5';
        }
    }

    /**
     * Настройка валидации формы
     * @param {HTMLElement} form - Элемент формы
     * @param {Object} rules - Правила валидации
     */
    static setupFormValidation(form, rules = {}) {
        if (!form) return;

        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this, rules[this.name] || {});
            });

            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });

        // Функция валидации поля
        function validateField(field, rules) {
            const value = field.value.trim();
            let isValid = true;
            let errorMessage = '';

            // Проверка обязательности
            if (rules.required && !value) {
                isValid = false;
                errorMessage = 'Это поле обязательно для заполнения';
            }

            // Проверка минимальной длины
            if (rules.minLength && value.length < rules.minLength) {
                isValid = false;
                errorMessage = `Минимальная длина ${rules.minLength} символов`;
            }

            // Проверка максимальной длины
            if (rules.maxLength && value.length > rules.maxLength) {
                isValid = false;
                errorMessage = `Максимальная длина ${rules.maxLength} символов`;
            }

            // Проверка email
            if (rules.email && value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    isValid = false;
                    errorMessage = 'Введите корректный email';
                }
            }

            // Показать/скрыть ошибку
            if (!isValid) {
                showFieldError(field, errorMessage);
            } else {
                clearFieldError(field);
            }

            return isValid;
        }

        // Показать ошибку поля
        function showFieldError(field, message) {
            clearFieldError(field);
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            errorDiv.textContent = message;
            errorDiv.style.cssText = `
                color: #f44336;
                font-size: 12px;
                margin-top: 4px;
                animation: fadeIn 0.3s ease-in;
            `;

            field.parentNode.appendChild(errorDiv);
            field.style.borderColor = '#f44336';
        }

        // Очистить ошибку поля
        function clearFieldError(field) {
            const errorDiv = field.parentNode.querySelector('.field-error');
            if (errorDiv) {
                errorDiv.remove();
            }
            field.style.borderColor = '';
        }
    }

    /**
     * Плавная прокрутка к элементу
     * @param {HTMLElement} element - Целевой элемент
     * @param {number} offset - Смещение от верха
     */
    static scrollToElement(element, offset = 0) {
        if (!element) return;

        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }

    /**
     * Анимация появления элемента
     * @param {HTMLElement} element - Элемент для анимации
     * @param {string} animation - Тип анимации ('fade', 'slide', 'scale')
     */
    static animateElement(element, animation = 'fade') {
        if (!element) return;

        const animations = {
            fade: 'fadeIn 0.5s ease-out',
            slide: 'slideInUp 0.5s ease-out',
            scale: 'scaleIn 0.3s ease-out'
        };

        element.style.animation = animations[animation] || animations.fade;
        element.style.opacity = '0';
        element.style.transform = animation === 'slide' ? 'translateY(20px)' : 
                                animation === 'scale' ? 'scale(0.8)' : '';

        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = '';
        }, 10);
    }
}

// Экспорт для использования в других модулях
window.UIHelpers = UIHelpers; 