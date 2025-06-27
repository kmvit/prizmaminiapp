import os
import re
from typing import List, Dict
from datetime import datetime
from pathlib import Path

# PDF библиотеки
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

from bot.database.models import User


class PDFGenerator:
    """Генератор PDF страниц с текстом"""
    
    def __init__(self):
        self.template_dir = Path("template_pdf")
        self.fonts_dir = Path("fonts")  # Папка в корне проекта
        self.fallback_fonts_dir = Path("frontend/fonts")  # Резервная папка
        self._setup_fonts()
    
    def clean_markdown_text(self, text: str) -> str:
        """Очистка текста от markdown разметки и форматирование для PDF"""
        
        if not text or not text.strip():
            return ""
        
        # Удаляем ссылки в квадратных скобках [1], [2] и т.д.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Заменяем markdown заголовки на простые заголовки с переносами
        # Обрабатываем заголовки от более специфичных к менее специфичным
        text = re.sub(r'^#####\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)  # H5
        text = re.sub(r'^####\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)   # H4 - сохраняем весь текст
        text = re.sub(r'^###\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)    # H3
        text = re.sub(r'^##\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)     # H2
        text = re.sub(r'^#\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)      # H1
        
        # Удаляем жирный текст ** но оставляем содержимое
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        
        # Удаляем курсив * но оставляем содержимое
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        
        # Заменяем markdown списки на простые списки
        text = re.sub(r'^-\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        # НЕ удаляем нумерацию из заголовков! Убираем только из настоящих списков
        # Удаляем нумерацию только из строк, которые НЕ являются заголовками
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            # Проверяем, является ли строка заголовком с нумерацией
            if re.match(r'^\d+\.\s+(.+)$', line):
                # Если это короткая строка (скорее всего заголовок), оставляем как есть
                if len(line.strip()) < 80:
                    processed_lines.append(line)
                else:
                    # Это длинная строка - убираем нумерацию (это список)
                    processed_lines.append(re.sub(r'^\d+\.\s+(.+)$', r'\1', line))
            else:
                processed_lines.append(line)
        text = '\n'.join(processed_lines)
        
        # Убираем лишние пробелы и переносы
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Множественные переносы -> двойной
        text = re.sub(r'[ \t]+', ' ', text)  # Множественные пробелы -> одинарный
        
        # Специальная обработка цитат - добавляем отступы
        # Обрабатываем многострочные цитаты
        lines = text.split('\n')
        processed_lines = []
        in_quote = False
        
        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append('')
                continue
                
            # Проверяем начало цитаты
            if (line.startswith('«') and not line.endswith('»')) or (line.startswith('"') and not line.endswith('"')):
                in_quote = True
                processed_lines.append('   ' + line)
            # Проверяем окончание цитаты
            elif in_quote and (line.endswith('»') or line.endswith('"')):
                in_quote = False
                processed_lines.append('   ' + line)
            # Строка внутри цитаты
            elif in_quote:
                processed_lines.append('   ' + line)
            # Однострочная цитата
            elif (line.startswith('«') and line.endswith('»')) or (line.startswith('"') and line.endswith('"')):
                processed_lines.append('   ' + line)
            else:
                processed_lines.append(line)
        
        text = '\n'.join(processed_lines)
        
        # Убираем пробелы в начале и конце строк, но сохраняем отступы цитат
        lines = []
        for line in text.split('\n'):
            # Сохраняем отступы для цитат
            if line.lstrip().startswith('«') or line.lstrip().startswith('"'):
                lines.append(line.rstrip())  # Убираем только пробелы справа
            else:
                lines.append(line.strip())  # Убираем пробелы с обеих сторон
        text = '\n'.join(lines)
        
        # Убираем пустые строки в начале и конце
        text = text.strip()
        
        return text
    
    def _setup_fonts(self):
        """Настройка шрифтов для русского текста"""
        try:
            # Попытка регистрации шрифта Inter (основной шрифт шаблонов)
            inter_paths = [
                self.fonts_dir / "Inter-Regular.ttf",
                self.fonts_dir / "Inter-Regular.otf",
                self.fonts_dir / "Inter/Inter-Regular.otf",
                self.fonts_dir / "Inter.ttf", 
                self.fonts_dir / "Inter-Medium.ttf",
                self.fonts_dir / "Inter/Inter-Medium.otf"
            ]
            
            inter_bold_paths = [
                self.fonts_dir / "Inter-Bold.ttf",
                self.fonts_dir / "Inter-Bold.otf",
                self.fonts_dir / "Inter/Inter-Bold.otf",
                self.fonts_dir / "Inter-SemiBold.ttf",
                self.fonts_dir / "Inter/Inter-SemiBold.otf"
            ]
            
            # Регистрируем Inter Regular
            inter_registered = False
            for path in inter_paths:
                if path.exists():
                    pdfmetrics.registerFont(TTFont('Inter', str(path)))
                    self.default_font = 'Inter'
                    inter_registered = True
                    print(f"✅ Зарегистрирован шрифт Inter: {path}")
                    break
            
            # Регистрируем Inter Bold
            for path in inter_bold_paths:
                if path.exists():
                    pdfmetrics.registerFont(TTFont('Inter-Bold', str(path)))
                    self.bold_font = 'Inter-Bold'
                    print(f"✅ Зарегистрирован шрифт Inter-Bold: {path}")
                    break
            
            # Если Inter не найден, используем резервные шрифты
            if not inter_registered:
                # Попробуем OpenSans из frontend/fonts (поддерживает кириллицу)
                opensans_path = self.fallback_fonts_dir / "OpenSans-Regular.ttf"
                montserrat_path = self.fallback_fonts_dir / "Montserrat-Regular.ttf"
                
                if opensans_path.exists():
                    pdfmetrics.registerFont(TTFont('OpenSans', str(opensans_path)))
                    self.default_font = 'OpenSans'
                    print(f"⚠️ Inter не найден, используем OpenSans: {opensans_path}")
                elif montserrat_path.exists():
                    pdfmetrics.registerFont(TTFont('Montserrat', str(montserrat_path)))
                    self.default_font = 'Montserrat'
                    print(f"⚠️ Inter не найден, используем Montserrat: {montserrat_path}")
                else:
                    self.default_font = 'Helvetica'  # Системный шрифт
                    print("⚠️ Кастомные шрифты не найдены, используем системный Helvetica")
            
            # Устанавливаем жирный шрифт по умолчанию, если не найден Inter-Bold
            if not hasattr(self, 'bold_font'):
                if inter_registered:
                    self.bold_font = 'Inter'  # Используем обычный Inter
                else:
                    self.bold_font = self.default_font
                    
        except Exception as e:
            print(f"⚠️ Ошибка при регистрации шрифтов: {e}")
            self.default_font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
    
    def create_text_page(self, text: str, template_path: Path, page_width: float = A4[0], page_height: float = A4[1]) -> BytesIO:
        """Создание PDF страницы с текстом на основе готового шаблона"""
        
        if not template_path.exists():
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")
        
        # Очищаем текст от markdown разметки
        text = self.clean_markdown_text(text)
        
        # Создаем текстовый слой
        text_buffer = BytesIO()
        text_canvas = canvas.Canvas(text_buffer, pagesize=A4)
        
        # Настройки для текста
        text_canvas.setFont(self.default_font, 11)
        
        # Область для текста (отступы от краев)
        left_margin = 75
        right_margin = 75
        top_margin = 100
        bottom_margin = 100
        
        text_width = page_width - left_margin - right_margin
        text_height = page_height - top_margin - bottom_margin
        
        # Разбиваем текст на строки
        lines = text.strip().split('\n')
        y_position = page_height - top_margin
        line_height = 14
        
        for line in lines:
            line = line.strip()
            if not line:
                y_position -= line_height / 2  # Пустая строка - меньший отступ
                continue
            
            # Определяем уровень заголовка
            heading_level = 0
            is_quote = line.startswith('   «') or line.startswith('   "') or line.startswith('«') or line.startswith('"')
            
            # Заголовки первого уровня - большие вопросы (основные разделы)
            if (len(line) < 100 and 
                any(keyword in line.lower() for keyword in ['как вы мыслите', 'кто вы по типу', 'какие паттерны', 'как вы воспринимаете'])):
                heading_level = 1
            # Заголовки второго уровня - разделы и подразделы
            elif (line.endswith(':') and len(line) < 80 
                  or any(keyword in line.lower() for keyword in ['подкрепляющая цитата', 'утверждения пользователя', 'как они блокируют', 'как перфекционизм', 'ограничивающие убеждения', 'репетитивные модели'])
                  or (len(line) < 60 and not line.startswith('•') and not line.startswith('-') and not is_quote and not line.endswith('.'))):
                heading_level = 2
            
            if heading_level == 1:
                # Заголовок первого уровня - крупный, жирный шрифт, выровнен по левому краю
                text_canvas.setFont(self.bold_font, 18)
                # Выравниваем заголовок по левому краю
                x_position = left_margin
                text_canvas.drawString(x_position, y_position, line)
                y_position -= line_height * 2
                text_canvas.setFont(self.default_font, 11)  # Возвращаем обычный шрифт
            elif heading_level == 2:
                # Заголовок второго уровня - обычный размер, без жирного
                text_canvas.setFont(self.default_font, 13)
                x_position = left_margin
                text_canvas.drawString(x_position, y_position, line)
                y_position -= line_height * 1.3
                text_canvas.setFont(self.default_font, 11)  # Возвращаем обычный шрифт
            elif is_quote:
                # Цитата - курсив и отступ
                text_canvas.setFont(self.bold_font, 10)
                # Убираем добавленные отступы из регекса для правильного отображения
                quote_text = line.lstrip()
                words = quote_text.split(' ')
                current_line = ""
                quote_margin = left_margin + 20  # Дополнительный отступ для цитат
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    test_width = text_canvas.stringWidth(test_line, self.default_font, 10)
                    
                    if test_width <= (text_width - 20):  # Учитываем дополнительный отступ
                        current_line = test_line
                    else:
                        if current_line:
                            text_canvas.drawString(quote_margin, y_position, current_line)
                            y_position -= line_height
                        current_line = word
                
                if current_line:
                    text_canvas.drawString(quote_margin, y_position, current_line)
                    y_position -= line_height
                
                text_canvas.setFont(self.default_font, 11)  # Возвращаем обычный размер
            else:
                # Обычный текст - переносим длинные строки
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    test_width = text_canvas.stringWidth(test_line, self.default_font, 11)
                    
                    if test_width <= text_width:
                        current_line = test_line
                    else:
                        # Выводим накопленную строку
                        if current_line:
                            text_canvas.drawString(left_margin, y_position, current_line)
                            y_position -= line_height
                        current_line = word
                
                # Выводим последнюю строку
                if current_line:
                    text_canvas.drawString(left_margin, y_position, current_line)
                    y_position -= line_height
            
            # Проверяем, не вышли ли за пределы страницы
            if y_position < bottom_margin:
                break
        
        text_canvas.save()
        text_buffer.seek(0)
        
        # Загружаем шаблон и накладываем текст
        template_reader = PdfReader(str(template_path))
        template_page = template_reader.pages[0]
        
        # Создаем текстовый PDF из буфера
        text_reader = PdfReader(text_buffer)
        text_page = text_reader.pages[0]
        
        # Накладываем текст на шаблон
        template_page.merge_page(text_page)
        
        # Сохраняем результат в буфер
        result_buffer = BytesIO()
        writer = PdfWriter()
        writer.add_page(template_page)
        writer.write(result_buffer)
        result_buffer.seek(0)
        
        return result_buffer
    
    def combine_pdfs(self, pdf_parts: List[Path], output_path: Path) -> bool:
        """Объединение PDF файлов в один"""
        
        try:
            writer = PdfWriter()
            
            for pdf_path in pdf_parts:
                if pdf_path.exists():
                    reader = PdfReader(str(pdf_path))
                    for page in reader.pages:
                        writer.add_page(page)
                else:
                    print(f"⚠️ Файл не найден: {pdf_path}")
                    return False
            
            # Сохраняем объединенный PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при объединении PDF: {e}")
            return False


class ReportGenerator:
    """Генератор PDF отчетов"""
    
    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.template_dir = Path("template_pdf")
        self.pdf_generator = PDFGenerator()
    
    def create_text_report(self, user: User, analysis_result: Dict) -> str:
        """Создание текстового отчета с результатами анализа (временно вместо PDF)"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"prizma_report_{user.telegram_id}_{timestamp}.txt"
        filepath = self.reports_dir / filename
        
        # Очищаем тексты от markdown разметки
        page3_clean = self.pdf_generator.clean_markdown_text(analysis_result.get('page3_analysis', 'Анализ не доступен'))
        page4_clean = self.pdf_generator.clean_markdown_text(analysis_result.get('page4_analysis', 'Анализ не доступен'))
        page5_clean = self.pdf_generator.clean_markdown_text(analysis_result.get('page5_analysis', 'Анализ не доступен'))
        
        # Формируем содержимое отчета для всех трех страниц
        report_content = f"""
СТРАНИЦА 3: КТО ВЫ ПО ТИПУ ЛИЧНОСТИ?
{'=' * 60}

{page3_clean}

{'=' * 60}

СТРАНИЦА 4: КАК ВЫ МЫСЛИТЕ И ПРИНИМАЕТЕ РЕШЕНИЯ?
{'=' * 60}

{page4_clean}

{'=' * 60}

СТРАНИЦА 5: КАКИЕ ПАТТЕРНЫ ОГРАНИЧИВАЮТ ВАШЕ РАЗВИТИЕ?
{'=' * 60}

{page5_clean}

{'=' * 60}
"""
        
        # Сохраняем файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(filepath)
    
    def create_pdf_report(self, user: User, analysis_result: Dict) -> str:
        """Создание полного PDF отчета на основе шаблонов"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"prizma_report_{user.telegram_id}_{timestamp}.pdf"
        output_path = self.reports_dir / filename
        
        try:
            # Создаем временные PDF файлы для страниц 3, 4, 5 на основе шаблонов
            temp_dir = self.reports_dir / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            temp_files = []
            
            # Создаем PDF для страницы 3 на основе шаблона 3.pdf
            if analysis_result.get('page3_analysis'):
                template3_path = self.template_dir / "3.pdf"
                page3_buffer = self.pdf_generator.create_text_page(
                    analysis_result['page3_analysis'], 
                    template3_path
                )
                page3_path = temp_dir / "page3_temp.pdf"
                with open(page3_path, 'wb') as f:
                    f.write(page3_buffer.getvalue())
                temp_files.append(page3_path)
            
            # Создаем PDF для страницы 4 на основе шаблона 4.pdf
            if analysis_result.get('page4_analysis'):
                template4_path = self.template_dir / "4.pdf"
                page4_buffer = self.pdf_generator.create_text_page(
                    analysis_result['page4_analysis'], 
                    template4_path
                )
                page4_path = temp_dir / "page4_temp.pdf"
                with open(page4_path, 'wb') as f:
                    f.write(page4_buffer.getvalue())
                temp_files.append(page4_path)
            
            # Создаем PDF для страницы 5 на основе шаблона 5.pdf
            if analysis_result.get('page5_analysis'):
                template5_path = self.template_dir / "5.pdf"
                page5_buffer = self.pdf_generator.create_text_page(
                    analysis_result['page5_analysis'], 
                    template5_path
                )
                page5_path = temp_dir / "page5_temp.pdf"
                with open(page5_path, 'wb') as f:
                    f.write(page5_buffer.getvalue())
                temp_files.append(page5_path)
            
            # Составляем список всех PDF файлов в правильном порядке
            pdf_parts = [
                self.template_dir / "1.pdf",  # Неизменная страница 1
                self.template_dir / "2.pdf",  # Неизменная страница 2
                temp_dir / "page3_temp.pdf",  # Наша страница 3 с наложенным текстом
                temp_dir / "page4_temp.pdf",  # Наша страница 4 с наложенным текстом
                temp_dir / "page5_temp.pdf",  # Наша страница 5 с наложенным текстом
                self.template_dir / "6.pdf",  # Неизменная страница 6
                self.template_dir / "7.pdf",  # Неизменная страница 7
            ]
            
            # Объединяем все PDF файлы
            success = self.pdf_generator.combine_pdfs(pdf_parts, output_path)
            
            # Очищаем временные файлы
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            temp_dir.rmdir() if temp_dir.exists() and not list(temp_dir.iterdir()) else None
            
            if success:
                print(f"✅ PDF отчет создан: {output_path}")
                return str(output_path)
            else:
                raise Exception("Ошибка при объединении PDF файлов")
                
        except Exception as e:
            print(f"❌ Ошибка при создании PDF отчета: {e}")
            # Возвращаемся к текстовому отчету в случае ошибки
            return self.create_text_report(user, analysis_result) 