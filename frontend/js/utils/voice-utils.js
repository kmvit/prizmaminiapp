/**
 * Voice Utils - Утилиты для голосового ввода
 * Работа с микрофоном и транскрипция голоса
 */

class VoiceUtils {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recognition = null;
        this.onTranscriptionUpdate = null;
        this.onTranscriptionComplete = null;
    }

    /**
     * Начать голосовую транскрипцию
     * @param {Function} onUpdate - Callback для обновления транскрипции
     * @param {Function} onComplete - Callback для завершения транскрипции
     * @returns {Promise<void>}
     */
    static async startVoiceTranscription(onUpdate, onComplete) {
        try {
            console.log('🎤 Начинаем голосовую транскрипцию...');
            
            // Проверить поддержку Web Speech API
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                throw new Error('Голосовой ввод не поддерживается в этом браузере');
            }

            // Создать экземпляр распознавания
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();

            // Настройка параметров
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ru-RU';

            let finalTranscript = '';
            let interimTranscript = '';

            // Обработка результатов
            recognition.onresult = function(event) {
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                    } else {
                        interimTranscript = transcript;
                    }
                }

                const fullTranscript = finalTranscript + interimTranscript;
                
                // Обновить UI
                if (onUpdate) {
                    onUpdate(fullTranscript.trim());
                }

                // Показать индикатор транскрипции
                VoiceUtils.showTranscriptionIndicator(fullTranscript.trim());
            };

            // Обработка ошибок
            recognition.onerror = function(event) {
                console.error('❌ Ошибка распознавания речи:', event.error);
                VoiceUtils.hideTranscriptionIndicator();
                
                if (window.TelegramWebApp) {
                    window.TelegramWebApp.showAlert(`Ошибка распознавания: ${event.error}`);
                }
            };

            // Обработка завершения
            recognition.onend = function() {
                console.log('🎤 Распознавание завершено');
                VoiceUtils.hideTranscriptionIndicator();
                
                if (onComplete) {
                    onComplete(finalTranscript.trim());
                }
            };

            // Начать распознавание
            recognition.start();
            
            // Показать подсказку
            VoiceUtils.showVoiceInputHint();
            
            // Тактильная обратная связь
            if (window.TelegramWebApp) {
                window.TelegramWebApp.hapticFeedback('medium');
            }

        } catch (error) {
            console.error('❌ Ошибка запуска голосового ввода:', error);
            throw error;
        }
    }

    /**
     * Остановить голосовую транскрипцию
     */
    static stopVoiceTranscription() {
        try {
            console.log('🛑 Останавливаем голосовую транскрипцию...');
            
            // Остановить все активные распознавания
            if (window.speechRecognition) {
                window.speechRecognition.stop();
            }
            
            VoiceUtils.hideTranscriptionIndicator();
            
            // Тактильная обратная связь
            if (window.TelegramWebApp) {
                window.TelegramWebApp.hapticFeedback('light');
            }
            
        } catch (error) {
            console.error('❌ Ошибка остановки голосового ввода:', error);
        }
    }

    /**
     * Показать индикатор транскрипции
     * @param {string} text - Текст транскрипции
     */
    static showTranscriptionIndicator(text = '') {
        // Удалить существующий индикатор
        VoiceUtils.hideTranscriptionIndicator();

        // Создать индикатор
        const indicator = document.createElement('div');
        indicator.id = 'voice-transcription-indicator';
        indicator.innerHTML = `
            <div class="voice-indicator">
                <div class="voice-icon">
                    <div class="voice-wave">
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                    </div>
                </div>
                <div class="voice-text">
                    <div class="voice-status">Записываем...</div>
                    <div class="voice-transcript">${text}</div>
                </div>
                <button class="voice-stop-btn" onclick="VoiceUtils.stopVoiceTranscription()">
                    <span>⏹️</span>
                </button>
            </div>
        `;

        // Добавить стили
        const style = document.createElement('style');
        style.textContent = `
            .voice-indicator {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.9);
                color: white;
                padding: 16px 20px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                gap: 12px;
                z-index: 1000;
                min-width: 280px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                animation: slideUp 0.3s ease-out;
            }
            
            .voice-icon {
                flex-shrink: 0;
            }
            
            .voice-wave {
                display: flex;
                align-items: center;
                gap: 2px;
                height: 20px;
            }
            
            .wave-bar {
                width: 3px;
                background: #4CAF50;
                border-radius: 2px;
                animation: wave 1s ease-in-out infinite;
            }
            
            .wave-bar:nth-child(1) { animation-delay: 0s; height: 8px; }
            .wave-bar:nth-child(2) { animation-delay: 0.1s; height: 12px; }
            .wave-bar:nth-child(3) { animation-delay: 0.2s; height: 16px; }
            .wave-bar:nth-child(4) { animation-delay: 0.3s; height: 12px; }
            .wave-bar:nth-child(5) { animation-delay: 0.4s; height: 8px; }
            
            @keyframes wave {
                0%, 100% { height: 8px; }
                50% { height: 16px; }
            }
            
            @keyframes slideUp {
                from { transform: translateX(-50%) translateY(100%); opacity: 0; }
                to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
            
            .voice-text {
                flex: 1;
                min-width: 0;
            }
            
            .voice-status {
                font-size: 12px;
                opacity: 0.8;
                margin-bottom: 4px;
            }
            
            .voice-transcript {
                font-size: 14px;
                line-height: 1.3;
                word-wrap: break-word;
                max-height: 60px;
                overflow-y: auto;
            }
            
            .voice-stop-btn {
                background: #f44336;
                border: none;
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                transition: background 0.2s;
            }
            
            .voice-stop-btn:hover {
                background: #d32f2f;
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(indicator);
    }

    /**
     * Скрыть индикатор транскрипции
     */
    static hideTranscriptionIndicator() {
        const indicator = document.getElementById('voice-transcription-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Обновить текст транскрипции
     * @param {string} text - Новый текст
     */
    static updateTranscriptionIndicator(text) {
        const transcriptElement = document.querySelector('.voice-transcript');
        if (transcriptElement) {
            transcriptElement.textContent = text;
        }
    }

    /**
     * Показать подсказку для голосового ввода
     */
    static showVoiceInputHint() {
        const hint = document.createElement('div');
        hint.id = 'voice-input-hint';
        hint.innerHTML = `
            <div class="voice-hint">
                <div class="hint-icon">🎤</div>
                <div class="hint-text">
                    <strong>Голосовой ввод активен</strong><br>
                    Говорите четко и не спеша
                </div>
            </div>
        `;

        const style = document.createElement('style');
        style.textContent = `
            .voice-hint {
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #2196F3;
                color: white;
                padding: 12px 16px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 8px;
                z-index: 1000;
                font-size: 14px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                animation: fadeIn 0.3s ease-out;
            }
            
            .hint-icon {
                font-size: 20px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
                to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(hint);

        // Убрать подсказку через 3 секунды
        setTimeout(() => {
            if (hint.parentNode) {
                hint.remove();
            }
        }, 3000);
    }

    /**
     * Проверить поддержку голосового ввода
     * @returns {Object} Информация о поддержке
     */
    static checkVoiceSupport() {
        const support = {
            speechRecognition: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
            getUserMedia: !!navigator.mediaDevices && !!navigator.mediaDevices.getUserMedia,
            mediaRecorder: !!window.MediaRecorder
        };

        console.log('🎤 Поддержка голосового ввода:', support);
        return support;
    }

    /**
     * Записать аудио через MediaRecorder
     * @param {Function} onDataAvailable - Callback для получения данных
     * @param {Function} onStop - Callback для завершения записи
     * @returns {Promise<void>}
     */
    static async recordAudio(onDataAvailable, onStop) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            const audioChunks = [];

            mediaRecorder.ondataavailable = function(event) {
                audioChunks.push(event.data);
                if (onDataAvailable) {
                    onDataAvailable(event.data);
                }
            };

            mediaRecorder.onstop = function() {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                if (onStop) {
                    onStop(audioBlob);
                }
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            return mediaRecorder;

        } catch (error) {
            console.error('❌ Ошибка записи аудио:', error);
            throw error;
        }
    }

    /**
     * Воспроизвести аудио
     * @param {Blob} audioBlob - Аудио данные
     * @returns {Promise<void>}
     */
    static async playAudio(audioBlob) {
        try {
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            
            return new Promise((resolve, reject) => {
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                    resolve();
                };
                audio.onerror = reject;
                audio.play();
            });
        } catch (error) {
            console.error('❌ Ошибка воспроизведения аудио:', error);
            throw error;
        }
    }

    /**
     * Получить длительность аудио
     * @param {Blob} audioBlob - Аудио данные
     * @returns {Promise<number>} Длительность в секундах
     */
    static async getAudioDuration(audioBlob) {
        try {
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            
            return new Promise((resolve) => {
                audio.onloadedmetadata = () => {
                    URL.revokeObjectURL(audioUrl);
                    resolve(audio.duration);
                };
            });
        } catch (error) {
            console.error('❌ Ошибка получения длительности аудио:', error);
            return 0;
        }
    }
}

// Экспорт для использования в других модулях
window.VoiceUtils = VoiceUtils; 