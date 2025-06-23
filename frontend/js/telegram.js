// Telegram Web App SDK Integration
import { WebApp } from '@twa-dev/sdk';

class TelegramWebApp {
    constructor() {
        this.tg = WebApp;
        this.init();
    }

    init() {
        // Инициализация Web App
        this.tg.ready();
        
        // Настройка темы
        this.setupTheme();
        
        // Настройка кнопок
        this.setupButtons();
        
        // Получение данных пользователя
        this.getUserData();
    }

    setupTheme() {
        // Адаптация под тему Telegram
        document.documentElement.style.setProperty('--tg-theme-bg-color', this.tg.themeParams.bg_color || '#ffffff');
        document.documentElement.style.setProperty('--tg-theme-text-color', this.tg.themeParams.text_color || '#000000');
        document.documentElement.style.setProperty('--tg-theme-hint-color', this.tg.themeParams.hint_color || '#999999');
        document.documentElement.style.setProperty('--tg-theme-button-color', this.tg.themeParams.button_color || '#2481cc');
        document.documentElement.style.setProperty('--tg-theme-button-text-color', this.tg.themeParams.button_text_color || '#ffffff');
    }

    setupButtons() {
        // Настройка главной кнопки
        this.tg.MainButton.setText('Продолжить');
        this.tg.MainButton.hide();
        
        // Настройка кнопки назад
        this.tg.BackButton.hide();
    }

    getUserData() {
        const user = this.tg.initDataUnsafe?.user;
        if (user) {
            console.log('Telegram User:', user);
            return {
                id: user.id,
                first_name: user.first_name,
                last_name: user.last_name,
                username: user.username,
                language_code: user.language_code
            };
        }
        return null;
    }

    showMainButton(text = 'Продолжить', callback = null) {
        this.tg.MainButton.setText(text);
        this.tg.MainButton.show();
        
        if (callback) {
            this.tg.MainButton.onClick(callback);
        }
    }

    hideMainButton() {
        this.tg.MainButton.hide();
    }

    showBackButton(callback = null) {
        this.tg.BackButton.show();
        
        if (callback) {
            this.tg.BackButton.onClick(callback);
        } else {
            this.tg.BackButton.onClick(() => window.history.back());
        }
    }

    hideBackButton() {
        this.tg.BackButton.hide();
    }

    sendData(data) {
        // Отправка данных в Telegram Bot
        this.tg.sendData(JSON.stringify(data));
    }

    showAlert(message) {
        this.tg.showAlert(message);
    }

    showConfirm(message, callback) {
        this.tg.showConfirm(message, callback);
    }

    hapticFeedback(type = 'medium') {
        // Тактильная обратная связь
        this.tg.HapticFeedback.impactOccurred(type);
    }

    expandViewport() {
        // Развернуть viewport
        this.tg.expand();
    }

    close() {
        // Закрыть Web App
        this.tg.close();
    }

    openTelegramLink(url) {
        // Открыть ссылку в Telegram
        this.tg.openTelegramLink(url);
    }

    openLink(url) {
        // Открыть внешнюю ссылку
        this.tg.openLink(url);
    }
}

// Создаем глобальный экземпляр
window.telegramApp = new TelegramWebApp();

export default TelegramWebApp; 