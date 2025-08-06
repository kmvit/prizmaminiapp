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
            const response = await fetch(`${this.baseUrl}/user/${userId}/profile`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
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
            const response = await fetch(`${this.baseUrl}/user/${userId}/current-question`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
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
            
            // Открываем ссылку напрямую
            if (window.TelegramWebApp) {
                window.TelegramWebApp.openLink(endpoint);
                return { success: true, method: 'telegram' };
            } else {
                // Для браузера открываем в новой вкладке
                window.open(endpoint, '_blank');
                return { success: true, method: 'browser' };
            }
        } catch (error) {
            console.error('❌ Ошибка скачивания отчета:', error);
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
}

// Экспорт для использования в других модулях
window.ApiClient = ApiClient; 