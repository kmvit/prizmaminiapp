/**
 * API Client - Работа с серверными API
 * Клиент для взаимодействия с бэкендом
 */

class ApiClient {
    static baseUrl = '/api'; // Базовый URL для API
    
    /**
     * Получить прогресс пользователя
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Прогресс пользователя
     */
    static async getUserProgress(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/progress`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка получения прогресса:', error);
            throw error;
        }
    }

    /**
     * Получить профиль пользователя
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Профиль пользователя
     */
    static async getUserProfile(userId) {
        try {
            const url = `${this.baseUrl}/user/${userId}/profile`;
            console.log('🌐 Запрос профиля к API:', url);
            
            const response = await fetch(url);
            console.log('📡 Ответ API статус:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Ошибка API:', response.status, errorText);
                throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('📦 Данные профиля от API:', data);
            return data;
        } catch (error) {
            console.error('❌ Ошибка получения профиля:', error);
            throw error;
        }
    }

    /**
     * Сохранить профиль пользователя
     * @param {number} userId - ID пользователя
     * @param {Object} profile - Данные профиля
     * @returns {Promise<Object>} Результат сохранения
     */
    static async saveUserProfile(userId, profile) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/profile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(profile)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка сохранения профиля:', error);
            throw error;
        }
    }

    /**
     * Получить текущий вопрос
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Текущий вопрос
     */
    static async getCurrentQuestion(userId) {
        try {
            const url = `${this.baseUrl}/user/${userId}/current-question`;
            console.log('🌐 Запрос к API:', url);
            
            const response = await fetch(url);
            console.log('📡 Ответ API статус:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Ошибка API:', response.status, errorText);
                throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('📦 Данные от API:', data);
            return data;
        } catch (error) {
            console.error('❌ Ошибка получения вопроса:', error);
            throw error;
        }
    }

    /**
     * Отправить ответ на вопрос
     * @param {number} userId - ID пользователя
     * @param {string} answer - Ответ пользователя
     * @returns {Promise<Object>} Результат отправки
     */
    static async submitAnswer(userId, answer) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/answer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text_answer: answer,
                    answer_type: 'text'
                })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка отправки ответа:', error);
            throw error;
        }
    }

    /**
     * Сгенерировать бесплатный отчет
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Результат генерации
     */
    static async generateReport(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/generate-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка генерации отчета:', error);
            throw error;
        }
    }

    /**
     * Сгенерировать премиум отчет
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Результат генерации
     */
    static async generatePremiumReport(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/generate-premium-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка генерации премиум отчета:', error);
            throw error;
        }
    }

    /**
     * Получить статус отчетов
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Статус отчетов
     */
    static async getReportsStatus(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/reports-status`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка получения статуса отчетов:', error);
            throw error;
        }
    }

    /**
     * Начать премиум оплату
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Результат инициации оплаты
     */
    static async startPremiumPayment(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/start-premium-payment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка начала оплаты:', error);
            throw error;
        }
    }

    /**
     * Скачать отчет
     * @param {number} userId - ID пользователя
     * @param {string} reportType - Тип отчета ('free' или 'premium')
     * @returns {Promise<Object>} Результат скачивания
     */
    static async downloadReport(userId, reportType) {
        try {
            // Используем правильный эндпоинт для скачивания
            const endpoint = reportType === 'premium' 
                ? `${this.baseUrl}/download/premium-report/${userId}`
                : `${this.baseUrl}/download/report/${userId}`;
            
            console.log(`📥 Скачивание отчета: ${endpoint}`);
            
            // Для премиум отчетов всегда используем принудительное скачивание
            const downloadUrl = reportType === 'premium' 
                ? `${endpoint}?download=1&source=telegram&t=${Date.now()}`
                : `${endpoint}?download=1&source=telegram&t=${Date.now()}`;
            
            console.log(`📥 URL для скачивания: ${downloadUrl}`);
            
            // Открываем ссылку напрямую
            if (window.TelegramWebApp) {
                window.TelegramWebApp.openLink(downloadUrl);
                return { success: true, method: 'telegram', url: downloadUrl };
            } else {
                // Для браузера открываем в новой вкладке
                window.open(downloadUrl, '_blank');
                return { success: true, method: 'browser', url: downloadUrl };
            }
        } catch (error) {
            console.error('❌ Ошибка скачивания отчета:', error);
            throw error;
        }
    }

    /**
     * Сбросить тест пользователя
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Результат сброса
     */
    static async resetTest(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/reset-test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка сброса теста:', error);
            throw error;
        }
    }

    /**
     * Остановить генерацию отчета
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Результат остановки
     */
    static async stopReportGeneration(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/stop-report-generation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка остановки генерации отчета:', error);
            throw error;
        }
    }

    /**
     * Получить таймер спецпредложения
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Информация о таймере
     */
    static async getSpecialOfferTimer(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/special-offer-timer`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка получения таймера спецпредложения:', error);
            throw error;
        }
    }

    /**
     * Сбросить таймер спецпредложения
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Результат сброса
     */
    static async resetSpecialOfferTimer(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/reset-special-offer-timer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка сброса таймера спецпредложения:', error);
            throw error;
        }
    }

    /**
     * Универсальный метод для HTTP запросов
     * @param {string} endpoint - Конечная точка API
     * @param {Object} options - Опции запроса
     * @returns {Promise<Object>} Результат запроса
     */
    static async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`❌ API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * Получить таймер спецпредложения
     * @param {number} userId - ID пользователя
     * @returns {Promise<Object>} Информация о таймере
     */
    static async getSpecialOfferTimer(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/user/${userId}/special-offer-timer`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('❌ Ошибка получения таймера спецпредложения:', error);
            throw error;
        }
    }
}

// Экспорт для использования в других модулях
window.ApiClient = ApiClient; 