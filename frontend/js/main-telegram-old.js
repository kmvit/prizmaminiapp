/**
 * Main Telegram App - Модульная версия
 * Роутинг и инициализация страниц с использованием модулей
 */

'use strict';

// Импорт модулей страниц
import IndexPage from './pages/index-page.js';
import StepsPage from './pages/steps-page.js';
import LoginPage from './pages/login-page.js';
import QuestionPage from './pages/question-page.js';
import LoadingPage from './pages/loading-page.js';
import AnswersPage from './pages/answers-page.js';
import PricePage from './pages/price-page.js';
import PriceOfferPage from './pages/price-offer-page.js';
import PaymentPage from './pages/payment-page.js';
import DownloadPage from './pages/download-page.js';
import CompletePaymentPage from './pages/complete-payment-page.js';
import UncompletePaymentPage from './pages/uncomplete-payment-page.js';

$(function() {
    // ========================================
    // КОНФИГУРАЦИЯ
    // ========================================
    
    const API_BASE_URL = window.location.origin;
    
    // ========================================
    // ОСНОВНЫЕ УТИЛИТЫ
    // ========================================
    
    // Получение Telegram ID пользователя
    function getTelegramUserId() {
        return window.TelegramWebApp ? window.TelegramWebApp.getUserId() : 123456789;
    }

    // Проверка, работаем ли мы в Telegram Web App
    function isInTelegramWebApp() {
        return window.TelegramWebApp ? window.TelegramWebApp.isInTelegramWebApp() : false;
    }

    // Безопасная тактильная обратная связь
    function safeHapticFeedback(type = 'light') {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.hapticFeedback(type);
        }
    }

    // Безопасное отображение алерта
    function safeShowAlert(message) {
        if (window.TelegramWebApp) {
            window.TelegramWebApp.showAlert(message);
        } else {
            alert(message);
        }
    }

    // ========================================
    // РОУТИНГ И ИНИЦИАЛИЗАЦИЯ
    // ========================================
    
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
            
            // Инициализация соответствующей страницы
            initPage(currentPage);
        } else {
            console.log('⏳ TelegramWebApp not ready, retrying...');
            setTimeout(initTelegramApp, 100);
        }
    }

    /**
     * Инициализация страницы на основе модулей
     */
    function initPage(pageName) {
        try {
            switch(pageName) {
                case 'index':
                    IndexPage.init();
                    break;
                case 'steps':
                    StepsPage.init();
                    break;
                case 'login':
                    LoginPage.init();
                    break;
                case 'question':
                    console.log('🎯 Запускаем QuestionPage...');
                    QuestionPage.init();
                    break;
                case 'loading':
                    LoadingPage.init();
                    break;
                case 'answers':
                    AnswersPage.init();
                    break;
                case 'price':
                    PricePage.init();
                    break;
                case 'price-offer':
                    PriceOfferPage.init();
                    break;
                case 'payment':
                    PaymentPage.init();
                    break;
                case 'download':
                    DownloadPage.init();
                    break;
                case 'complete-payment':
                    CompletePaymentPage.init();
                    break;
                case 'uncomplete-payment':
                    UncompletePaymentPage.init();
                    break;
                default:
                    console.log('❌ Неизвестная страница:', pageName);
                    // По умолчанию инициализируем главную страницу
                    IndexPage.init();
                    break;
            }
        } catch (error) {
            console.error('❌ Ошибка при инициализации страницы:', error);
        }
    }

    // ========================================
    // ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    // ========================================
    
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
    
    // Проверка параметра startapp при запуске
    function checkStartApp() {
        try {
            const startParam = window.Telegram.WebApp.initDataUnsafe.start_param;
            if (startParam) {
                console.log('🚀 Обнаружен параметр запуска:', startParam);
                
                // Проверяем успешную оплату (с ID или без)
                if (startParam === 'payment_success' || startParam.startsWith('payment_success_')) {
                    console.log('💰 Обнаружена успешная оплата, перенаправляем на complete-payment');
                    window.location.href = 'complete-payment.html';
                    return;
                }
                
                // Проверяем неуспешную оплату
                if (startParam === 'payment_failed' || startParam.startsWith('payment_failed_')) {
                    console.log('❌ Обнаружена неуспешная оплата, перенаправляем на uncomplete-payment');
                    window.location.href = 'uncomplete-payment.html';
                    return;
                }
                
                console.log('📝 Неизвестный параметр запуска:', startParam);
            }
        } catch (error) {
            console.error('❌ Ошибка при проверке параметра запуска:', error);
        }
    }

    // Проверка параметра startapp при загрузке страницы
    function checkStartParamOnLoad() {
        try {
            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe) {
                checkStartApp();
            } else {
                console.log('⏳ Telegram WebApp не готов, откладываем проверку параметра запуска');
                setTimeout(checkStartParamOnLoad, 100);
            }
        } catch (error) {
            console.error('❌ Ошибка при проверке параметра запуска при загрузке:', error);
        }
    }

    // Определение текущей страницы
    function getCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        
        if (!filename || filename === 'index.html' || filename === '') {
            return 'index';
        }
        
        // Убираем расширение .html
        const pageName = filename.replace('.html', '');
        
        // Маппинг имен файлов на имена страниц
        const pageMapping = {
            'index': 'index',
            'steps': 'steps',
            'login': 'login',
            'question': 'question',
            'loading': 'loading',
            'answers': 'answers',
            'price': 'price',
            'price-offer': 'price-offer',
            'payment': 'payment',
            'download': 'download',
            'complete-payment': 'complete-payment',
            'uncomplete-payment': 'uncomplete-payment'
        };
        
        return pageMapping[pageName] || 'index';
    }

    // Безопасная инициализация Telegram App
    function safeInitTelegramApp() {
        if (appInitialized) {
            console.log('⚠️ TelegramApp уже инициализирован');
            return;
        }
        
        try {
            initTelegramApp();
            appInitialized = true;
        } catch (error) {
            console.error('❌ Ошибка при инициализации TelegramApp:', error);
        }
    }

    // ========================================
    // ЗАПУСК ПРИЛОЖЕНИЯ
    // ========================================
    
    // Проверяем параметр запуска при загрузке
    checkStartParamOnLoad();
    
    // Запускаем инициализацию с задержкой
    setTimeout(safeInitTelegramApp, 100);
    
    // Дополнительная попытка инициализации через 1 секунду
    setTimeout(safeInitTelegramApp, 1000);
    
    // Финальная попытка инициализации через 3 секунды
    setTimeout(safeInitTelegramApp, 3000);
}); 