"""
Сервис для генерации персональных PDF отчетов
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.rl_config import defaultEncoding
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from bot.config import BASE_DIR
from bot.database.models import User, Answer
from loguru import logger


class ReportGenerator:
    """Генератор персональных PDF отчетов"""
    
    def __init__(self):
        self.reports_dir = BASE_DIR / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Настраиваем UTF-8 кодировку для ReportLab
        import reportlab.rl_config
        reportlab.rl_config.defaultEncoding = 'utf-8'
        
        # Сначала создаем базовые стили
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName='Times-Bold',  # По умолчанию используем Times
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB')
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontName='Times-Bold',  # По умолчанию используем Times
            fontSize=16,
            spaceAfter=15,
            spaceBefore=20,
            textColor=colors.HexColor('#A23B72')
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontName='Times-Roman',  # По умолчанию используем Times
            fontSize=11,
            spaceAfter=10,
            leading=14
        )
        
        # Теперь пытаемся зарегистрировать лучшие шрифты с поддержкой кириллицы
        self._register_fonts()

    def _register_fonts(self):
        """Регистрация шрифтов с поддержкой кириллицы из папки проекта"""
        try:
            # Путь к папке со шрифтами
            fonts_dir = BASE_DIR / "frontend" / "fonts"
            
            # Список шрифтов для поиска (в порядке приоритета)
            font_files = [
                # DejaVu Sans - отличная поддержка кириллицы
                ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVu"),
                # Liberation Sans - хорошая альтернатива
                ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf", "Liberation"),
                # Roboto - современный шрифт
                ("Roboto-Regular.ttf", "Roboto-Bold.ttf", "Roboto"),
                # PT Sans - специально для кириллицы
                ("PTSans-Regular.ttf", "PTSans-Bold.ttf", "PTSans"),
                # Open Sans
                ("OpenSans-Regular.ttf", "OpenSans-Bold.ttf", "OpenSans"),
            ]
            
            # Пытаемся найти и зарегистрировать первый доступный шрифт
            for regular_file, bold_file, font_name in font_files:
                regular_path = fonts_dir / regular_file
                bold_path = fonts_dir / bold_file
                
                if regular_path.exists():
                    try:
                        # Регистрируем обычный шрифт
                        regular_font = TTFont(f'{font_name}-Regular', str(regular_path))
                        pdfmetrics.registerFont(regular_font)
                        
                        # Регистрируем жирный шрифт
                        bold_font_name = f'{font_name}-Bold'
                        if bold_path.exists():
                            bold_font = TTFont(bold_font_name, str(bold_path))
                        else:
                            # Если нет отдельного жирного файла, используем обычный
                            bold_font = TTFont(bold_font_name, str(regular_path))
                        
                        pdfmetrics.registerFont(bold_font)
                        
                        # Обновляем стили для использования зарегистрированного шрифта
                        self.title_style.fontName = bold_font_name
                        self.heading_style.fontName = bold_font_name  
                        self.normal_style.fontName = f'{font_name}-Regular'
                        
                        logger.info(f"✅ Зарегистрирован шрифт: {font_name} ({regular_path})")
                        return
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось зарегистрировать {regular_path}: {e}")
                        continue
            
            # Если в папке нет подходящих шрифтов, используем встроенные
            logger.warning("⚠️ Не найдены шрифты в папке frontend/fonts/, используем встроенные")
            self._use_builtin_fonts()
            
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации шрифтов: {e}")
            self._use_builtin_fonts()

    def _use_builtin_fonts(self):
        """Использование встроенных шрифтов с поддержкой кириллицы"""
        try:
            # Пытаемся использовать Helvetica для лучшей поддержки Unicode
            self.title_style.fontName = 'Helvetica-Bold'
            self.heading_style.fontName = 'Helvetica-Bold'
            self.normal_style.fontName = 'Helvetica'
            logger.info("✅ Используются встроенные шрифты Helvetica")
            logger.info("💡 Для лучшего отображения кириллицы рекомендуется скачать:")
            logger.info("   - DejaVu Sans: https://dejavu-fonts.github.io/")
            logger.info("   - PT Sans: https://fonts.google.com/specimen/PT+Sans") 
            logger.info("   - Roboto: https://fonts.google.com/specimen/Roboto")
            logger.info("   Поместите TTF файлы в папку frontend/fonts/")
        except:
            # Fallback к Times
            self.title_style.fontName = 'Times-Bold'
            self.heading_style.fontName = 'Times-Bold'
            self.normal_style.fontName = 'Times-Roman'
            logger.info("✅ Используются встроенные шрифты Times")
            logger.info("💡 Для лучшего отображения кириллицы рекомендуется скачать:")
            logger.info("   - DejaVu Sans: https://dejavu-fonts.github.io/")
            logger.info("   - PT Sans: https://fonts.google.com/specimen/PT+Sans") 
            logger.info("   - Roboto: https://fonts.google.com/specimen/Roboto")
            logger.info("   Поместите TTF файлы в папку frontend/fonts/")

    def _safe_text(self, text: str) -> str:
        """Безопасное преобразование текста для PDF с поддержкой кириллицы"""
        if not text:
            return ""
        
        try:
            # Убеждаемся что текст в UTF-8
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            
            # Нормализуем unicode
            import unicodedata
            text = unicodedata.normalize('NFC', text)
            
            # Заменяем проблемные символы
            text = text.replace('\n', '<br/>')
            text = text.replace('\r', '')
            text = text.replace('\t', ' ')
            
            # Экранируем HTML символы
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            # Возвращаем обратно наши br теги
            text = text.replace('&lt;br/&gt;', '<br/>')
            
            # Проверяем, что все символы можно отобразить
            # Заменяем неподдерживаемые символы
            safe_chars = []
            for char in text:
                try:
                    # Проверяем, что символ можно кодировать
                    char.encode('utf-8')
                    safe_chars.append(char)
                except UnicodeEncodeError:
                    safe_chars.append('?')
            
            result = ''.join(safe_chars)
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Проблема с кодировкой текста: {e}")
            # Fallback - принудительное кодирование
            try:
                return str(text).encode('utf-8', errors='replace').decode('utf-8')
            except:
                return "Ошибка кодировки"

    async def generate_report(self, user: User, answers: List[Answer]) -> str:
        """Генерировать персональный отчет пользователя"""
        
        try:
            # Создаем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prizma_report_{user.telegram_id}_{timestamp}.pdf"
            filepath = self.reports_dir / filename
            
            # Создаем PDF документ
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=50
            )
            
            # Строим содержимое отчета
            story = []
            
            # Заголовок
            story.append(Paragraph(self._safe_text("ПСИХОЛОГИЧЕСКАЯ РАСШИФРОВКА ЛИЧНОСТИ"), self.title_style))
            story.append(Spacer(1, 20))
            
            # Основная информация
            story.extend(self._build_user_info(user, answers))
            story.append(Spacer(1, 30))
            
            # Краткое резюме
            story.extend(self._build_summary(user, answers))
            story.append(Spacer(1, 20))
            
            # Анализ ответов
            story.extend(self._build_answers_analysis(answers))
            story.append(Spacer(1, 20))
            
            # Рекомендации
            story.extend(self._build_recommendations(user, answers))
            story.append(Spacer(1, 20))
            
            # Футер
            story.extend(self._build_footer())
            
            # Генерируем PDF
            doc.build(story)
            
            logger.info(f"📄 Отчет сгенерирован: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            raise

    def _build_user_info(self, user: User, answers: List[Answer]) -> List:
        """Блок с информацией о пользователе"""
        content = []
        
        # Формируем имя пользователя
        user_name = self._get_user_display_name(user)
        
        # Формируем возраст
        age_display = self._get_user_age_display(user)
        
        # Формируем пол
        gender_display = self._get_user_gender_display(user)
        
        # Количество ответов
        answer_count = f"{len(answers)} из {15 if not user.is_paid else 50} вопросов"
        
        # Таблица с основной информацией
        data = [
            [self._safe_text('Имя:'), self._safe_text(user_name)],
            [self._safe_text('Возраст:'), self._safe_text(age_display)],
            [self._safe_text('Пол:'), self._safe_text(gender_display)],
            [self._safe_text('Ответов дано:'), self._safe_text(answer_count)],
            [self._safe_text('Дата анализа:'), self._safe_text(datetime.now().strftime("%d %B %Y"))],
            [self._safe_text('Версия отчёта:'), self._safe_text('Базовая расшифровка (15 вопросов)' if not user.is_paid else 'Полная расшифровка (50 вопросов)')],
            [self._safe_text('Сервис:'), self._safe_text('PRIZMA • Персональный ИИ-анализ')],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), self.heading_style.fontName),
            ('FONTNAME', (1, 0), (1, -1), self.normal_style.fontName),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        content.append(table)
        return content

    def _get_user_display_name(self, user: User) -> str:
        """Получить отображаемое имя пользователя"""
        # Приоритет: name (если заполнено) -> first_name + last_name -> first_name -> telegram_id
        if user.name and user.name.strip():
            return user.name.strip()
        
        full_name_parts = []
        if user.first_name and user.first_name.strip():
            full_name_parts.append(user.first_name.strip())
        if user.last_name and user.last_name.strip():
            full_name_parts.append(user.last_name.strip())
        
        if full_name_parts:
            return " ".join(full_name_parts)
        
        return f"Пользователь {user.telegram_id}"

    def _get_user_age_display(self, user: User) -> str:
        """Получить отображение возраста пользователя"""
        if user.age and isinstance(user.age, int) and user.age > 0:
            # Правильное склонение для русского языка
            if user.age % 10 == 1 and user.age % 100 != 11:
                return f"{user.age} год"
            elif user.age % 10 in [2, 3, 4] and user.age % 100 not in [12, 13, 14]:
                return f"{user.age} года"
            else:
                return f"{user.age} лет"
        return "Не указан"

    def _get_user_gender_display(self, user: User) -> str:
        """Получить отображение пола пользователя"""
        if user.gender and user.gender.strip():
            gender = user.gender.strip().lower()
            
            # Нормализуем различные варианты написания
            if gender in ['м', 'мужской', 'муж', 'male', 'm']:
                return "Мужской"
            elif gender in ['ж', 'женский', 'жен', 'female', 'f']:
                return "Женский"
            else:
                return user.gender.capitalize()
        
        return "Не указан"

    def _build_summary(self, user: User, answers: List[Answer]) -> List:
        """Блок краткого резюме"""
        content = []
        
        content.append(Paragraph(self._safe_text("КРАТКОЕ РЕЗЮМЕ"), self.heading_style))
        
        # Генерируем персональное резюме на основе ответов
        summary_text = self._generate_personality_summary(answers)
        content.append(Paragraph(self._safe_text(summary_text), self.normal_style))
        
        return content

    def _build_answers_analysis(self, answers: List[Answer]) -> List:
        """Анализ ответов пользователя"""
        content = []
        
        content.append(Paragraph(self._safe_text("АНАЛИЗ ВАШИХ ОТВЕТОВ"), self.heading_style))
        
        # Показываем все доступные ответы пользователя
        for i, answer in enumerate(answers, 1):
            content.append(Paragraph(self._safe_text(f"<b>Вопрос {i}:</b>"), self.normal_style))
            
            # Обрезаем длинные ответы
            answer_text = answer.text_answer[:200] + "..." if len(answer.text_answer) > 200 else answer.text_answer
            content.append(Paragraph(self._safe_text(f"Ваш ответ: {answer_text}"), self.normal_style))
            
            # Добавляем ИИ-анализ если есть
            if answer.ai_analysis:
                analysis_text = answer.ai_analysis[:300] + "..." if len(answer.ai_analysis) > 300 else answer.ai_analysis
                content.append(Paragraph(self._safe_text(f"<i>Анализ: {analysis_text}</i>"), self.normal_style))
            
            content.append(Spacer(1, 10))
        
        return content

    def _build_recommendations(self, user: User, answers: List[Answer]) -> List:
        """Персональные рекомендации"""
        content = []
        
        content.append(Paragraph(self._safe_text("ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ"), self.heading_style))
        
        recommendations = [
            "Развивайте навыки самоанализа - ведите дневник размышлений 10 минут в день",
            "Практикуйте осознанность - уделяйте внимание своим эмоциям и реакциям", 
            "Ставьте конкретные цели - разбивайте большие задачи на выполнимые шаги",
            "Развивайте эмоциональный интеллект - учитесь понимать свои и чужие эмоции",
            "Заботьтесь о балансе работы и отдыха - это ключ к долгосрочному успеху"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            content.append(Paragraph(self._safe_text(f"{i}. {rec}"), self.normal_style))
        
        return content

    def _build_footer(self) -> List:
        """Футер отчета"""
        content = []
        
        content.append(Spacer(1, 30))
        content.append(Paragraph(self._safe_text("ПОДДЕРЖКА"), self.heading_style))
        content.append(Paragraph(self._safe_text("Остались вопросы? Telegram: @prizma_support"), self.normal_style))
        content.append(Paragraph(self._safe_text("Email: support@prizma.ai"), self.normal_style))
        content.append(Spacer(1, 20))
        
        footer_text = f"© 2025 PRIZMA. Все права защищены. | Дата создания: {datetime.now().strftime('%d.%m.%Y, %H:%M')} МСК"
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontName=self.normal_style.fontName,
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        content.append(Paragraph(self._safe_text(footer_text), footer_style))
        
        return content

    def _generate_personality_summary(self, answers: List[Answer]) -> str:
        """Генерируем краткое описание личности на основе ответов"""
        
        # Простой анализ на основе длины и содержания ответов
        total_words = sum(len(answer.text_answer.split()) for answer in answers)
        avg_length = total_words / len(answers) if answers else 0
        
        if avg_length > 50:
            detail_level = "детально и вдумчиво"
        elif avg_length > 20:
            detail_level = "обстоятельно"
        else:
            detail_level = "кратко и по существу"
            
        summary = f"""
        Вы отвечали на вопросы {detail_level}, что говорит о вашем подходе к самоанализу. 
        Ваш психологический профиль указывает на человека, способного к размышлениям и 
        саморефлексии. Вы демонстрируете готовность к честному самоанализу и открытость 
        к новым знаниям о себе.
        
        Основные черты: склонность к самоанализу, готовность к развитию, честность в 
        ответах. Количество завершенных вопросов ({len(answers)}) показывает ваше 
        стремление к полному пониманию своей личности.
        """
        
        return summary.strip()

# Создаем экземпляр генератора
report_generator = ReportGenerator() 