// Конфигурация для Telegram Mini App
window.AppConfig = {
    // API endpoints
    api: {
        baseUrl: 'http://localhost:8080/api', // Замените на реальный URL backend
        endpoints: {
            saveProfile: '/user/profile',
            saveAnswers: '/user/answers',
            generateReport: '/user/report',
            processPayment: '/payment/create',
            checkPayment: '/payment/status'
        }
    },
    
    // Telegram Bot настройки
    telegram: {
        botToken: '', // Будет заполнено на backend
        webAppUrl: 'http://localhost:8080', // Замените на реальный домен
    },
    
    // Настройки опроса
    survey: {
        totalQuestions: 15,
        maxAnswerLength: 1000,
        voiceRecordingMaxDuration: 300, // 5 минут в секундах
        questions: [
            "Расскажите о своих основных целях и мечтах. Что для вас наиболее важно в жизни?",
            "Опишите ваши отношения с близкими людьми. Как вы выстраиваете доверие?",
            "Какие эмоции вы испытываете чаще всего? Как вы справляетесь со стрессом?",
            "Расскажите о вашей работе или деятельности. Что приносит вам удовлетворение?",
            "Как вы принимаете важные решения? На что опираетесь?",
            "Опишите ваши страхи и беспокойства. Что вас больше всего тревожит?",
            "Какие у вас сильные стороны? В чем вы чувствуете себя уверенно?",
            "Расскажите о ваших хобби и интересах. Что вас вдохновляет?",
            "Как вы видите себя через 5 лет? Какие планы у вас есть?",
            "Опишите ваш идеальный день. Как бы вы хотели проводить время?",
            "Какие ценности для вас наиболее важны? Что вы никогда не нарушите?",
            "Расскажите о моментах, когда вы чувствовали себя наиболее счастливым.",
            "Как вы относитесь к переменам в жизни? Легко ли вам адаптироваться?",
            "Опишите ваши отношения с самим собой. Как вы к себе относитесь?",
            "Что бы вы хотели изменить в своей жизни? О чем мечтаете?"
        ]
    },
    
    // Настройки оплаты
    payment: {
        currency: 'RUB',
        prices: {
            free: 0,
            premium: 299
        }
    },
    
    // Настройки для разработки
    development: {
        enableLogging: true,
        mockAPI: true, // Включить mock API для тестирования
        skipPayment: false // Пропустить оплату для тестирования
    }
};

// Вспомогательные функции для работы с API
window.AppAPI = {
    async request(endpoint, options = {}) {
        const url = `${AppConfig.api.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        const requestOptions = { ...defaultOptions, ...options };
        
        // Добавляем Telegram данные в заголовки
        if (window.TelegramWebApp && window.TelegramWebApp.isInTelegram()) {
            requestOptions.headers['X-Telegram-Init-Data'] = window.TelegramWebApp.tg.initData;
        }
        
        try {
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            
            // Fallback для разработки
            if (AppConfig.development.mockAPI) {
                return this.mockResponse(endpoint, options);
            }
            
            throw error;
        }
    },
    
    mockResponse(endpoint, options) {
        // Mock responses для тестирования
        const mockData = {
            '/user/profile': { success: true, id: 'mock-user-id' },
            '/user/answers': { success: true, id: 'mock-answers-id' },
            '/user/report': { 
                success: true, 
                report: 'Mock отчет о личности пользователя...',
                downloadUrl: 'mock-download-url'
            },
            '/payment/create': { 
                success: true, 
                paymentUrl: 'mock-payment-url',
                paymentId: 'mock-payment-id'
            },
            '/payment/status': { success: true, status: 'paid' }
        };
        
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(mockData[endpoint] || { success: true });
            }, 1000); // Имитация задержки сети
        });
    }
}; 