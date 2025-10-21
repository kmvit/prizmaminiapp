/**
 * Download Utils - Утилиты для скачивания файлов
 * Различные методы загрузки файлов с обработкой ошибок
 */

class DownloadUtils {
    /**
     * Скачать отчет
     * @param {number} userId - ID пользователя
     * @param {string} reportType - Тип отчета ('free' или 'premium')
     * @param {Object} options - Дополнительные опции
     * @returns {Promise<Object>} Результат скачивания
     */
    static async downloadReport(userId, reportType, options = {}) {
        try {
            console.log(`📥 Начинаем скачивание отчета: ${reportType} для пользователя ${userId}`);
            
            // Для премиум отчетов показываем специальное сообщение
            if (reportType === 'premium') {
                console.log('💎 Скачивание премиум отчета - используем принудительное скачивание');
                
                // Показываем инструкции для премиум отчета
                if (options.showInstructions && window.TelegramWebApp) {
                    window.TelegramWebApp.showAlert(
                        '💎 Скачивание премиум отчета\n\n' +
                        '📱 Файл будет автоматически скачан на ваше устройство.\n' +
                        '📄 Имя файла: prizma-premium-report-' + userId + '.pdf\n\n' +
                        '💡 Если скачивание не началось автоматически, проверьте настройки браузера.'
                    );
                }
            }
            
            // Используем упрощенный метод скачивания
            const result = await ApiClient.downloadReport(userId, reportType);
            
            console.log('✅ Файл успешно скачан:', result);
            
            // Дополнительная тактильная обратная связь для премиум отчетов
            if (reportType === 'premium' && window.TelegramWebApp) {
                try {
                    window.TelegramWebApp.hapticFeedback('heavy');
                } catch (e) {
                    console.log('⚠️ Не удалось выполнить hapticFeedback:', e);
                }
            }
            
            return result;

        } catch (error) {
            console.error('❌ Ошибка скачивания отчета:', error);
            
            // Показать ошибку пользователю
            if (window.TelegramWebApp) {
                window.TelegramWebApp.showAlert(`Ошибка скачивания: ${error.message}`);
            } else {
                alert(`Ошибка скачивания: ${error.message}`);
            }
            
            throw error;
        }
    }

    /**
     * Скачивание через Telegram
     * @param {string} url - URL для скачивания
     * @returns {Promise<void>}
     */
    static async downloadViaTelegram(url) {
        if (!window.TelegramWebApp || !window.TelegramWebApp.isInTelegram()) {
            throw new Error('Не в Telegram Web App');
        }

        return new Promise((resolve, reject) => {
            try {
                // Открыть ссылку в Telegram
                window.TelegramWebApp.openLink(url);
                resolve();
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Скачивание через Fetch API
     * @param {string} url - URL для скачивания
     * @param {string} filename - Имя файла
     * @returns {Promise<void>}
     */
    static async downloadViaFetch(url, filename) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            // Создать ссылку для скачивания
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename || 'report.pdf';
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Очистить URL
            window.URL.revokeObjectURL(downloadUrl);
            
        } catch (error) {
            throw new Error(`Ошибка fetch: ${error.message}`);
        }
    }

    /**
     * Скачивание через прямую ссылку
     * @param {string} url - URL для скачивания
     * @returns {Promise<void>}
     */
    static async downloadViaDirectLink(url) {
        return new Promise((resolve, reject) => {
            try {
                // Открыть в новой вкладке
                const link = document.createElement('a');
                link.href = url;
                link.target = '_blank';
                link.style.display = 'none';
                
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                resolve();
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Показать инструкции по скачиванию
     * @param {string} url - URL для скачивания
     */
    static showDownloadInstructions(url) {
        const message = `
📥 Инструкция по скачиванию:

1. Скопируйте ссылку ниже
2. Вставьте в браузер
3. Файл начнет скачиваться

Ссылка: ${url}

Если скачивание не началось автоматически, нажмите правой кнопкой мыши на ссылку и выберите "Сохранить как..."
        `;

        if (window.TelegramWebApp) {
            window.TelegramWebApp.showAlert(message);
        } else {
            alert(message);
        }
    }

    /**
     * Проверить поддержку скачивания
     * @returns {Object} Информация о поддержке
     */
    static checkDownloadSupport() {
        const support = {
            telegram: !!window.TelegramWebApp && window.TelegramWebApp.isInTelegram(),
            fetch: !!window.fetch,
            download: !!document.createElement('a').download,
            blob: !!window.Blob,
            url: !!window.URL && !!window.URL.createObjectURL
        };

        console.log('📋 Поддержка скачивания:', support);
        return support;
    }

    /**
     * Скачать файл с прогрессом
     * @param {string} url - URL файла
     * @param {string} filename - Имя файла
     * @param {Function} onProgress - Callback для прогресса
     * @returns {Promise<void>}
     */
    static async downloadWithProgress(url, filename, onProgress) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentLength = response.headers.get('content-length');
            const total = parseInt(contentLength, 10);
            let loaded = 0;

            const reader = response.body.getReader();
            const chunks = [];

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                chunks.push(value);
                loaded += value.length;
                
                if (onProgress && total) {
                    const progress = (loaded / total) * 100;
                    onProgress(progress, loaded, total);
                }
            }

            // Создать blob из чанков
            const blob = new Blob(chunks);
            const downloadUrl = window.URL.createObjectURL(blob);
            
            // Скачать файл
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            window.URL.revokeObjectURL(downloadUrl);

        } catch (error) {
            throw new Error(`Ошибка скачивания с прогрессом: ${error.message}`);
        }
    }

    /**
     * Скачать несколько файлов
     * @param {Array} files - Массив файлов для скачивания
     * @returns {Promise<Array>} Результаты скачивания
     */
    static async downloadMultipleFiles(files) {
        const results = [];
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            try {
                console.log(`📥 Скачивание файла ${i + 1}/${files.length}: ${file.name}`);
                
                const result = await this.downloadReport(
                    file.userId, 
                    file.reportType, 
                    file.options
                );
                
                results.push({
                    success: true,
                    filename: file.name,
                    result
                });
                
            } catch (error) {
                console.error(`❌ Ошибка скачивания файла ${file.name}:`, error);
                results.push({
                    success: false,
                    filename: file.name,
                    error: error.message
                });
            }
        }
        
        return results;
    }

    /**
     * Получить размер файла
     * @param {string} url - URL файла
     * @returns {Promise<number>} Размер в байтах
     */
    static async getFileSize(url) {
        try {
            const response = await fetch(url, { method: 'HEAD' });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentLength = response.headers.get('content-length');
            return contentLength ? parseInt(contentLength, 10) : 0;
        } catch (error) {
            console.error('❌ Ошибка получения размера файла:', error);
            return 0;
        }
    }

    /**
     * Форматировать размер файла
     * @param {number} bytes - Размер в байтах
     * @returns {string} Отформатированный размер
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Б';
        
        const k = 1024;
        const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Экспорт для использования в других модулях
window.DownloadUtils = DownloadUtils; 