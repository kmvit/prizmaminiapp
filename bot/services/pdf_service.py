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
from reportlab.lib.colors import Color

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
        
        # ДОПОЛНИТЕЛЬНАЯ ОЧИСТКА: убираем оставшиеся markdown символы где угодно
        text = re.sub(r'#{1,6}\s*', '', text)  # Убираем # символы и пробелы после них
        text = re.sub(r'^\s*#{1,6}$', '', text, flags=re.MULTILINE)  # Убираем строки только с ###
        
        # Убираем markdown разделители (строки из дефисов, равенств, подчеркиваний)
        text = re.sub(r'^[-=_]{3,}\s*$', '', text, flags=re.MULTILINE)  # Убираем разделители ---
        text = re.sub(r'^[\s]*[-=_]+[\s]*$', '', text, flags=re.MULTILINE)  # Убираем разделители с пробелами
        
        # Убираем остатки markdown форматирования
        text = re.sub(r'[`~]', '', text)  # Убираем бэктики и тильды
        text = re.sub(r'\\\w+', '', text)  # Убираем escape последовательности \word
        
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
        
        # ОБРАБОТКА MARKDOWN ТАБЛИЦ
        text = self._process_markdown_tables(text)
        
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
    
    def _process_markdown_tables(self, text: str) -> str:
        """Обработка markdown таблиц и преобразование в читаемый формат"""
        
        lines = text.split('\n')
        processed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Проверяем, является ли строка началом таблицы (содержит несколько |)
            if '|' in line and line.count('|') >= 2:
                table_lines = []
                
                # Собираем все строки таблицы
                while i < len(lines) and ('|' in lines[i] or not lines[i].strip()):
                    current_line = lines[i].strip()
                    if current_line:  # Пропускаем пустые строки
                        table_lines.append(current_line)
                    i += 1
                
                # Обрабатываем таблицу
                formatted_table = self._format_table(table_lines)
                if formatted_table:
                    processed_lines.extend(formatted_table)
                    processed_lines.append('')  # Добавляем пустую строку после таблицы
            else:
                processed_lines.append(line)
                i += 1
        
        return '\n'.join(processed_lines)
    
    def _format_table(self, table_lines: list) -> list:
        """Форматирует markdown таблицу в читаемый текст"""
        
        if not table_lines:
            return []
        
        # Удаляем разделительные строки (содержат только |, -, :, пробелы)
        data_lines = []
        for line in table_lines:
            if not re.match(r'^[\|\-\:\s]+$', line):
                data_lines.append(line)
        
        if not data_lines:
            return []
        
        # Парсим строки таблицы
        parsed_rows = []
        for line in data_lines:
            # Убираем крайние | и разбиваем по |
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            # Убираем пустые ячейки в конце
            while cells and not cells[-1]:
                cells.pop()
            if cells:  # Добавляем только непустые строки
                parsed_rows.append(cells)
        
        if not parsed_rows:
            return []
        
        # Форматируем таблицу
        formatted_lines = []
        
        # Добавляем заголовок таблицы (первая строка)
        if parsed_rows:
            header = parsed_rows[0]
            formatted_lines.append('')
            
            # Форматируем заголовок
            header_text = ' | '.join(header)
            formatted_lines.append(f'ЗАГОЛОВКИ: {header_text}')
            formatted_lines.append('')
            
            # Форматируем строки данных
            for i, row in enumerate(parsed_rows[1:], 1):
                # Дополняем строку пустыми ячейками до длины заголовка
                while len(row) < len(header):
                    row.append('')
                
                formatted_lines.append(f'Строка {i}:')
                for j, (col_name, cell_value) in enumerate(zip(header, row)):
                    if cell_value.strip():  # Показываем только заполненные ячейки
                        formatted_lines.append(f'  • {col_name}: {cell_value}')
                    else:
                        formatted_lines.append(f'  • {col_name}: [не указано]')
                formatted_lines.append('')
        
        return formatted_lines
    
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
    
    def _wrap_line(self, text_canvas, text, font_name, font_size, max_width):
        """Разбивает строку на физические строки по ширине с учётом шрифта."""
        from reportlab.pdfbase.pdfmetrics import stringWidth
        
        # Если текст уже помещается в одну строку
        if stringWidth(text, font_name, font_size) <= max_width:
            return [text]
        
        words = text.split(' ')
        lines = []
        current = ''
        
        for word in words:
            test = (current + ' ' + word).strip() if current else word
            width = stringWidth(test, font_name, font_size)
            
            if width > max_width:
                if current:
                    lines.append(current)
                # Если одно слово слишком длинное, разбиваем его
                if stringWidth(word, font_name, font_size) > max_width:
                    # Разбиваем длинное слово по символам
                    chars = list(word)
                    temp_word = ''
                    for char in chars:
                        test_char = temp_word + char
                        if stringWidth(test_char, font_name, font_size) <= max_width:
                            temp_word = test_char
                        else:
                            if temp_word:
                                lines.append(temp_word)
                            temp_word = char
                    if temp_word:
                        current = temp_word
                    else:
                        current = ''
                else:
                    current = word
            else:
                current = test
        
        if current:
            lines.append(current)
        
        return lines

    def create_text_pages(self, text: str, template_path: Path, page_width: float = A4[0], page_height: float = A4[1]) -> list:
        """Создание одной или нескольких PDF страниц с текстом на основе шаблона. Корректный перенос по ширине и стилю, цвет и шрифт по ТЗ."""
        if not template_path.exists():
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")
        text = self.clean_markdown_text(text)
        
        # Проверяем, не пустой ли текст после очистки
        if not text or not text.strip():
            print("⚠️ Текст пустой после очистки, пропускаем создание страниц")
            return []
        
        lines = text.strip().split('\n')
        print(f"   📄 Обрабатываем {len(lines)} строк текста")
        

        left_margin = 75
        right_margin = 75
        top_margin = 100
        bottom_margin = 100
        text_width = page_width - left_margin - right_margin
        text_height = page_height - top_margin - bottom_margin
        
       
        # Высоты для разных типов строк
        line_height = 14
        h1_height = 24  # чуть больше для 18pt
        h2_height = 18  # чуть больше для 14pt
        quote_height = line_height
        # Цвета
        main_color = Color(1/255, 28/255, 92/255)  # #011C5C
        h1_color = Color(218/255, 5/255, 52/255)   # #DA0534 - Красный
        h2_color = Color(2/255, 88/255, 185/255)   # #0258B9 - Синий
        # Для реального разбиения считаем высоту каждой физической строки
        pages = []
        current_lines = []
        current_height = 0
        
        # Фильтруем пустые строки и строки только с пробелами
        filtered_lines = []
        for line in lines:
            if line.strip():  # Добавляем только непустые строки
                filtered_lines.append(line)
        
        if not filtered_lines:
            print("⚠️ Нет непустых строк для обработки, пропускаем создание страниц")
            return []
        
        for line in filtered_lines:
            l = line.strip()
            
            if not l:
                h = line_height / 2
                kind = 'empty'
                wrapped = ['']
            else:
                heading_level = 0
                is_quote = l.startswith('   «') or l.startswith('   "') or l.startswith('«') or l.startswith('"')
                # Проверяем маркированные списки (•, -) и нумерованные списки (1., 2., 3. и т.д.)
                is_list_item = (l.startswith('•') or l.startswith('-') or 
                               re.match(r'^\d+\.\s+', l))
                
                # Заголовок 1 - основные разделы
                h1_keywords = [
                    'как вы мыслите', 'кто вы по типу', 'какие паттерны', 'как вы воспринимаете',
                    'анализ big five', 'определение типа mbti', 'архетипическая структура',
                    'когнитивный профиль', 'эмоциональный интеллект', 'система ценностей',
                    'коммуникативный стиль', 'мотивационные драйверы', 'теневые аспекты',
                    'природные таланты', 'приобретённые компетенции', 'ресурсные состояния',
                    'ограничивающие убеждения', 'когнитивные искажения', 'эмоциональные триггеры'
                ]
                if (len(l) < 120 and any(keyword in l.lower() for keyword in h1_keywords)):
                    heading_level = 1
                else:
                    # Заголовок 2 - подразделы  
                    h2_keywords = [
                        'подкрепляющая цитата', 'утверждения пользователя', 'как они блокируют', 
                        'как перфекционизм', 'репетитивные модели', 'конкретные примеры',
                        'практические рекомендации', 'техники работы', 'упражнения'
                    ]
                    if (l.endswith(':') and len(l) < 100 
                          or any(keyword in l.lower() for keyword in h2_keywords)
                          or (len(l) < 80 and not is_list_item and not is_quote and not l.endswith('.') and not l.startswith('**') and not re.match(r'^\d+\.\s+', l))):
                        heading_level = 2
                if heading_level == 1:
                    h = h1_height
                    kind = 'h1'
                    wrapped = self._wrap_line(None, l, self.bold_font if hasattr(self, 'bold_font') else self.default_font, 18, text_width)
                elif heading_level == 2:
                    h = h2_height
                    kind = 'h2'
                    wrapped = self._wrap_line(None, l, self.default_font, 14, text_width)
                elif is_quote:
                    h = quote_height
                    kind = 'quote'
                    wrapped = self._wrap_line(None, l.lstrip(), self.bold_font if hasattr(self, 'bold_font') else self.default_font, 10, text_width - 20)
                elif is_list_item:
                    h = line_height
                    kind = 'list_item'
                    # Для списков используем отступ для продолжения строк
                    wrapped = self._wrap_line(None, l, self.default_font, 11, text_width - 20)
                else:
                    h = line_height
                    kind = 'text'
                    wrapped = self._wrap_line(None, l, self.default_font, 11, text_width)
            for wline in wrapped:
                if kind == 'empty':
                    wh = line_height / 2
                elif kind == 'h1':
                    wh = h1_height
                elif kind == 'h2':
                    wh = h2_height
                elif kind == 'quote':
                    wh = quote_height
                elif kind == 'list_item':
                    # Для элементов списка учитываем возможную длину строки
                    wh = line_height
                    # Если строка очень длинная, добавляем дополнительную высоту
                    if len(wline) > 100:
                        wh += line_height * 0.5
                    # Для нумерованных списков добавляем немного больше места
                    if re.match(r'^\d+\.\s+', wline):
                        wh += line_height * 0.2
                else:
                    wh = line_height
                    # Для обычного текста также учитываем длину
                    if len(wline) > 120:
                        wh += line_height * 0.3
                # Проверяем, поместится ли строка на текущей странице с учетом нижнего отступа
                # Добавляем дополнительный запас в 50px для безопасности
                if current_height + wh > text_height - 50 and current_lines:
                    pages.append(current_lines)
                    current_lines = []
                    current_height = 0
                # Для заголовков сохраняем тип
                if kind == 'h1':
                    current_lines.append((wline, kind, 'h1'))
                elif kind == 'h2':
                    current_lines.append((wline, kind, 'h2'))
                else:
                    current_lines.append((wline, kind, None))
                current_height += wh
        if current_lines:
            pages.append(current_lines)
        
        # Проверяем, что у нас есть страницы с контентом
        if not pages:
            print("⚠️ Нет страниц для отрисовки, пропускаем создание PDF")
            return []
        
        print(f"📄 Создано страниц для отрисовки: {len(pages)}")
        
        # Генерируем PDF для каждой страницы
        result_buffers = []
        for page_lines in pages:
            text_buffer = BytesIO()
            text_canvas = canvas.Canvas(text_buffer, pagesize=A4)
            y_position = page_height - top_margin
            
            for line, kind, header_type in page_lines:
                l = line.strip()
                
                # Убираем дублирующую проверку границ - она уже выполнена при разбиении на страницы
                # Все строки в page_lines гарантированно поместятся на странице
                
                if kind == 'empty':
                    y_position -= line_height / 2
                    continue
                if kind == 'h1':
                    # Добавляем отступ сверху для заголовка H1
                    y_position -= 10
                    text_canvas.setFont(self.bold_font if hasattr(self, 'bold_font') else self.default_font, 18)
                    text_canvas.setFillColor(h1_color)
                    x_position = left_margin
                    text_canvas.drawString(x_position, y_position, l)
                    y_position -= h1_height
                    text_canvas.setFont(self.default_font, 11)
                    text_canvas.setFillColor(main_color)
                elif kind == 'h2':
                    # Добавляем отступ сверху для заголовка H2
                    y_position -= 8
                    text_canvas.setFont(self.default_font, 14)
                    text_canvas.setFillColor(h2_color)
                    x_position = left_margin
                    text_canvas.drawString(x_position, y_position, l)
                    y_position -= h2_height
                    text_canvas.setFont(self.default_font, 11)
                    text_canvas.setFillColor(main_color)
                elif kind == 'quote':
                    text_canvas.setFont(self.bold_font if hasattr(self, 'bold_font') else self.default_font, 10)
                    text_canvas.setFillColor(main_color)
                    quote_margin = left_margin + 20
                    text_canvas.drawString(quote_margin, y_position, l)
                    y_position -= quote_height
                    text_canvas.setFont(self.default_font, 11)
                elif kind == 'list_item':
                    text_canvas.setFont(self.default_font, 11)
                    text_canvas.setFillColor(main_color)
                    # Для элементов списка используем отступ
                    list_margin = left_margin + 20
                    # Дополнительная проверка границ страницы
                    if y_position > bottom_margin:
                        # Для нумерованных списков используем немного больший отступ
                        if re.match(r'^\d+\.\s+', l):
                            list_margin = left_margin + 25
                        text_canvas.drawString(list_margin, y_position, l)
                        y_position -= line_height
                    else:
                        # Если текст не помещается, пропускаем его
                        print(f"⚠️ Элемент списка не помещается на странице: {l[:50]}...")
                        continue
                else:
                    text_canvas.setFont(self.default_font, 11)
                    text_canvas.setFillColor(main_color)
                    # Дополнительная проверка границ страницы
                    if y_position > bottom_margin:
                        text_canvas.drawString(left_margin, y_position, l)
                        y_position -= line_height
                    else:
                        # Если текст не помещается, пропускаем его
                        print(f"⚠️ Строка не помещается на странице: {l[:50]}...")
                        continue
            
            text_canvas.save()
            text_buffer.seek(0)
            template_reader = PdfReader(str(template_path))
            template_page = template_reader.pages[0]
            text_reader = PdfReader(text_buffer)
            text_page = text_reader.pages[0]
            template_page.merge_page(text_page)
            result_buffer = BytesIO()
            writer = PdfWriter()
            writer.add_page(template_page)
            writer.write(result_buffer)
            result_buffer.seek(0)
            result_buffers.append(result_buffer)
        return result_buffers

    # Оставляем старый create_text_page для обратной совместимости
    def create_text_page(self, text: str, template_path: Path, page_width: float = A4[0], page_height: float = A4[1]) -> BytesIO:
        """Создание одной PDF страницы (старый интерфейс)"""
        pages = self.create_text_pages(text, template_path, page_width, page_height)
        return pages[0] if pages else BytesIO()
    
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
    
    def create_custom_title_page(self, template_path: Path, user_name: str, completion_date: str) -> BytesIO:
        """Создание титульной страницы с данными пользователя"""
        
        if not template_path.exists():
            raise FileNotFoundError(f"Шаблон титульной страницы не найден: {template_path}")
        
        # Создаем текст с данными пользователя
        user_info_text = f"Создано для {user_name}\n{completion_date}"
        
        # Создаем PDF с текстом
        text_buffer = BytesIO()
        text_canvas = canvas.Canvas(text_buffer, pagesize=A4)
        
        # Настройки шрифта и цвета
        text_canvas.setFont(self.default_font, 12)
        main_color = Color(1/255, 28/255, 92/255)  # #011C5C
        
        # Позиция для текста по центру страницы, но на 200px ниже
        page_width, page_height = A4
        x_position = page_width / 2  # Центр по горизонтали
        y_position = (page_height / 2) - 200  # Центр по вертикали минус 200px
        
        # Рисуем новый текст
        text_canvas.setFillColor(main_color)
        text_canvas.setFont(self.default_font, 16)
        lines = user_info_text.split('\n')
        for line in lines:
            # Центрируем текст по горизонтали
            text_width = text_canvas.stringWidth(line, self.default_font, 16)
            centered_x = x_position - (text_width / 2)
            text_canvas.drawString(centered_x, y_position, line)
            y_position -= 25  # Увеличенный отступ между строками для шрифта 16px
        
        text_canvas.save()
        text_buffer.seek(0)
        
        # Объединяем с шаблоном
        template_reader = PdfReader(str(template_path))
        template_page = template_reader.pages[0]
        text_reader = PdfReader(text_buffer)
        text_page = text_reader.pages[0]
        template_page.merge_page(text_page)
        
        result_buffer = BytesIO()
        writer = PdfWriter()
        writer.add_page(template_page)
        writer.write(result_buffer)
        result_buffer.seek(0)
        
        return result_buffer


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
        """Создание полного PDF отчета на основе шаблонов, с переносом текста на доп. страницы шаблона 4.pdf"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"prizma_report_{user.telegram_id}_{timestamp}.pdf"
        output_path = self.reports_dir / filename
        try:
            temp_dir = self.reports_dir / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_files = []
            # Страница 3 (шаблон 3.pdf)
            if analysis_result.get('page3_analysis'):
                template3_path = self.template_dir / "3.pdf"
                page3_buffers = self.pdf_generator.create_text_pages(
                    analysis_result['page3_analysis'], template3_path)
                for i, buf in enumerate(page3_buffers):
                    page_path = temp_dir / f"page3_temp_{i+1}.pdf"
                    with open(page_path, 'wb') as f:
                        f.write(buf.getvalue())
                    temp_files.append(page_path)
            # Страница 4 (шаблон 4.pdf, с переносом)
            if analysis_result.get('page4_analysis'):
                template4_path = self.template_dir / "4.pdf"
                page4_buffers = self.pdf_generator.create_text_pages(
                    analysis_result['page4_analysis'], template4_path)
                for i, buf in enumerate(page4_buffers):
                    page_path = temp_dir / f"page4_temp_{i+1}.pdf"
                    with open(page_path, 'wb') as f:
                        f.write(buf.getvalue())
                    temp_files.append(page_path)
            # Страница 5 (шаблон 5.pdf, с переносом на 4.pdf)
            if analysis_result.get('page5_analysis'):
                template5_path = self.template_dir / "5.pdf"
                page5_buffers = self.pdf_generator.create_text_pages(
                    analysis_result['page5_analysis'], template5_path)
                for i, buf in enumerate(page5_buffers):
                    # первая страница — 5.pdf, остальные — 4.pdf
                    if i == 0:
                        page_path = temp_dir / f"page5_temp_1.pdf"
                        with open(page_path, 'wb') as f:
                            f.write(buf.getvalue())
                        temp_files.append(page_path)
                    else:
                        # для доп. страниц используем шаблон 4.pdf
                        template4_path = self.template_dir / "4.pdf"
                        buf4 = self.pdf_generator.create_text_pages(
                            '\n'.join(page5_buffers[i].getvalue().decode('latin1').split('\n')), template4_path)[0]
                        page_path = temp_dir / f"page5_temp_{i+1}.pdf"
                        with open(page_path, 'wb') as f:
                            f.write(buf4.getvalue())
                        temp_files.append(page_path)
            pdf_parts = [
                self.template_dir / "1.pdf",
                self.template_dir / "2.pdf",
            ]
            # Добавляем все страницы 3, 4, 5 (в нужном порядке)
            for f in temp_files:
                pdf_parts.append(f)
            pdf_parts += [
                self.template_dir / "6.pdf",
                self.template_dir / "7.pdf",
            ]
            success = self.pdf_generator.combine_pdfs(pdf_parts, output_path)
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
            return self.create_text_report(user, analysis_result)

    def create_free_basic_pdf_report(self, user: User, analysis_result: Dict) -> str:
        """
        Создание упрощенного бесплатного PDF отчета (2.5-3 страницы)
        Использует только базовые шаблоны из template_pdf
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"prizma_free_report_{user.telegram_id}_{timestamp}.pdf"
        output_path = self.reports_dir / filename
        
        try:
            temp_dir = self.reports_dir / "temp_free"
            temp_dir.mkdir(exist_ok=True)
            temp_files = []
            
            # Создаем страницы с анализом (используем шаблон 3.pdf для всех страниц)
            template3_path = self.template_dir / "3.pdf"
            
            # Страница 1: Тип личности
            if analysis_result.get('personality_type'):
                buffers = self.pdf_generator.create_text_pages(
                    analysis_result['personality_type'], template3_path)
                for i, buf in enumerate(buffers):
                    page_path = temp_dir / f"personality_{i+1}.pdf"
                    with open(page_path, 'wb') as f:
                        f.write(buf.getvalue())
                    temp_files.append(page_path)
            
            # Страница 2: Уникальность
            if analysis_result.get('uniqueness'):
                template4_path = self.template_dir / "4.pdf"
                buffers = self.pdf_generator.create_text_pages(
                    analysis_result['uniqueness'], template4_path)
                for i, buf in enumerate(buffers):
                    page_path = temp_dir / f"uniqueness_{i+1}.pdf"
                    with open(page_path, 'wb') as f:
                        f.write(buf.getvalue())
                    temp_files.append(page_path)
            
            # Страница 3: Ключевой инсайт
            if analysis_result.get('key_insight'):
                template5_path = self.template_dir / "5.pdf"
                buffers = self.pdf_generator.create_text_pages(
                    analysis_result['key_insight'], template5_path)
                for i, buf in enumerate(buffers):
                    page_path = temp_dir / f"insight_{i+1}.pdf"
                    with open(page_path, 'wb') as f:
                        f.write(buf.getvalue())
                    temp_files.append(page_path)
            
            # Собираем PDF: титульная + аналитические страницы + заключительные
            pdf_parts = [
                self.template_dir / "1.pdf",  # Титульная
            ]
            
            # Добавляем все аналитические страницы
            for f in temp_files:
                pdf_parts.append(f)
            
            # Добавляем заключительные страницы
            pdf_parts += [
                self.template_dir / "6.pdf",  # Информация о премиум версии
                self.template_dir / "7.pdf",  # Контакты
            ]
            
            # Объединяем все PDF
            success = self.pdf_generator.combine_pdfs(pdf_parts, output_path)
            
            # Очищаем временные файлы
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
            
            if success:
                print(f"✅ Бесплатный PDF отчет создан: {output_path}")
                return str(output_path)
            else:
                raise Exception("Ошибка при объединении PDF файлов")
                
        except Exception as e:
            print(f"❌ Ошибка при создании бесплатного PDF отчета: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: создаем текстовый отчет
            return self.create_text_report(user, analysis_result)

    def create_premium_pdf_report(self, user: User, analysis_result: Dict) -> str:
        """Создание платного PDF отчета с использованием template_pdf_premium шаблонов"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"prizma_premium_report_{user.telegram_id}_{timestamp}.pdf"
        output_path = self.reports_dir / filename
        
        try:
            # Создаем временные PDF файлы для всех страниц
            temp_dir = self.reports_dir / "temp_premium"
            temp_dir.mkdir(exist_ok=True)
            
            temp_files = []
            pdf_parts = []
            
            # Проверяем, есть ли постраничные данные (новая архитектура)
            individual_pages = analysis_result.get('individual_pages', {})
            
            if individual_pages:
                # НОВАЯ ЛОГИКА: Постраничная генерация с template_pdf_premium шаблонами
                print(f"📄 Создаем премиум PDF с {len(individual_pages)} отдельными страницами...")
                
                # Генерируем отчет по блокам с правильным чередованием статичных и динамических страниц
                pdf_parts = self._generate_premium_pdf_by_blocks(individual_pages, temp_dir, temp_files, user)
                    
                print(f"📊 Общее количество страниц в премиум PDF: {len(pdf_parts)} (статичные + ИИ)")
                
            else:
                # СТАРАЯ ЛОГИКА: Блочная генерация (6 блоков) - fallback
                print(f"📄 Нет постраничных данных, используем блочную генерацию...")
                
                premium_blocks = {
                    'premium_analysis': 'Основной анализ',
                    'premium_compensation': 'Компенсаторика',
                    'premium_prognosis': 'Прогностика', 
                    'premium_practical': 'Практическое приложение',
                    'premium_conclusion': 'Заключение',
                    'premium_appendix': 'Приложения'
                }
                
                template_path = self.template_dir / "3.pdf"  # Используем шаблон 3.pdf для всех блоков
                
                for block_key, block_name in premium_blocks.items():
                    if analysis_result.get(block_key):
                        print(f"📄 Создаем PDF для блока: {block_name}")
                        
                        # Используем create_text_pages для автоматического переноса длинного текста
                        block_buffers = self.pdf_generator.create_text_pages(
                            analysis_result[block_key], 
                            template_path
                        )
                        
                        # Обрабатываем все созданные страницы блока
                        for page_idx, block_buffer in enumerate(block_buffers):
                            if page_idx == 0:
                                block_path = temp_dir / f"{block_key}_temp.pdf"
                            else:
                                block_path = temp_dir / f"{block_key}_temp_{page_idx+1}.pdf"
                            
                            with open(block_path, 'wb') as f:
                                f.write(block_buffer.getvalue())
                            temp_files.append(block_path)
                
                # Составляем список всех PDF файлов в правильном порядке
                pdf_parts = []
                
                # Добавляем статические страницы в начале (если есть)
                if (self.template_dir / "1.pdf").exists():
                    pdf_parts.append(self.template_dir / "1.pdf")
                if (self.template_dir / "2.pdf").exists():
                    pdf_parts.append(self.template_dir / "2.pdf")
                
                # Добавляем все блоки платного анализа (включая дополнительные страницы)
                for block_key in premium_blocks.keys():
                    # Добавляем основную страницу блока
                    block_path = temp_dir / f"{block_key}_temp.pdf"
                    if block_path.exists():
                        pdf_parts.append(block_path)
                    
                    # Добавляем дополнительные страницы блока (если есть)
                    page_idx = 2  # Начинаем с 2-й страницы
                    while True:
                        additional_page = temp_dir / f"{block_key}_temp_{page_idx}.pdf"
                        if additional_page.exists():
                            pdf_parts.append(additional_page)
                            page_idx += 1
                        else:
                            break
                
                # Добавляем статические страницы в конце (если есть)
                if (self.template_dir / "6.pdf").exists():
                    pdf_parts.append(self.template_dir / "6.pdf")
                if (self.template_dir / "7.pdf").exists():
                    pdf_parts.append(self.template_dir / "7.pdf")
            
            # Объединяем все PDF файлы
            success = self.pdf_generator.combine_pdfs(pdf_parts, output_path)
            
            # Очищаем временные файлы
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            temp_dir.rmdir() if temp_dir.exists() and not list(temp_dir.iterdir()) else None
            
            if success:
                pages_count = len(individual_pages) if individual_pages else 6
                print(f"✅ Платный PDF отчет создан: {output_path} ({pages_count} страниц контента)")
                return str(output_path)
            else:
                raise Exception("Ошибка при объединении PDF файлов платного отчета")
                
        except Exception as e:
            print(f"❌ Ошибка при создании платного PDF отчета: {e}")
            # Возвращаемся к текстовому отчету в случае ошибки
            return self.create_premium_text_report(user, analysis_result)

    def create_premium_text_report(self, user: User, analysis_result: Dict) -> str:
        """Создание текстового платного отчета с результатами анализа (50 вопросов)"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"prizma_premium_report_{user.telegram_id}_{timestamp}.txt"
        filepath = self.reports_dir / filename
        
        # Очищаем тексты от markdown разметки
        premium_analysis = self.pdf_generator.clean_markdown_text(analysis_result.get('premium_analysis', 'Анализ не доступен'))
        premium_compensation = self.pdf_generator.clean_markdown_text(analysis_result.get('premium_compensation', 'Компенсаторика не доступна'))
        premium_prognosis = self.pdf_generator.clean_markdown_text(analysis_result.get('premium_prognosis', 'Прогностика не доступна'))
        premium_practical = self.pdf_generator.clean_markdown_text(analysis_result.get('premium_practical', 'Практическое приложение не доступно'))
        premium_conclusion = self.pdf_generator.clean_markdown_text(analysis_result.get('premium_conclusion', 'Заключение не доступно'))
        premium_appendix = self.pdf_generator.clean_markdown_text(analysis_result.get('premium_appendix', 'Приложения не доступны'))
        
        # Формируем содержимое платного отчета
        report_content = f"""
ПЛАТНЫЙ ОТЧЕТ PRIZMA (50 вопросов)
{'=' * 60}

ОСНОВНОЙ АНАЛИЗ (10 страниц)
{'=' * 60}

{premium_analysis}

{'=' * 60}

КОМПЕНСАТОРИКА (11 страниц)
{'=' * 60}

{premium_compensation}

{'=' * 60}

ПРОГНОСТИКА (6 страниц)
{'=' * 60}

{premium_prognosis}

{'=' * 60}

ПРАКТИЧЕСКОЕ ПРИЛОЖЕНИЕ (10 страниц)
{'=' * 60}

{premium_practical}

{'=' * 60}

ЗАКЛЮЧЕНИЕ (3 страницы)
{'=' * 60}

{premium_conclusion}

{'=' * 60}

ПРИЛОЖЕНИЯ (8 страниц)
{'=' * 60}

{premium_appendix}

{'=' * 60}
"""
        
        # Сохраняем файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(filepath)
    
    def _get_premium_block_template_mapping(self):
        """Возвращает соответствие между section_key и папкой с шаблонами"""
        return {
            "premium_analysis": "block-1",        # Психологический портрет
            "premium_strengths": "block-2",       # Сильные стороны и таланты  
            "premium_growth_zones": "block-3",    # Зоны роста
            "premium_compensation": "block-4",    # Компенсаторика
            "premium_interaction": "block-5",     # Взаимодействие с окружающими
            "premium_prognosis": "block-6",       # Прогностика
            "premium_practical": "block-7",       # Практическое приложение
            "premium_conclusion": "block-8",      # Заключение
            "premium_appendix": "block-9"         # Приложения
        }
    
    def _generate_premium_pdf_by_blocks(self, individual_pages: dict, temp_dir: Path, temp_files: list, user: User) -> list:
        """Генерирует премиум PDF с правильным чередованием статичных и динамических страниц"""
        
        pdf_parts = []
        premium_templates_dir = Path("template_pdf_premium")  # Папка с премиум шаблонами
        ai_template_path = self.template_dir / "3.pdf"  # Шаблон для ИИ ответов
        
        # Получаем mapping блоков
        block_mapping = self._get_premium_block_template_mapping()
        
        # Группируем страницы по секциям и сортируем
        pages_by_section = {}
        for page_key, page_data in individual_pages.items():
            section_key = page_data["section_key"]
            if section_key not in pages_by_section:
                pages_by_section[section_key] = []
            pages_by_section[section_key].append((page_key, page_data))
        
        # Сортируем секции в правильном порядке
        ordered_sections = [
            "premium_analysis", "premium_strengths", "premium_growth_zones", 
            "premium_compensation", "premium_interaction", "premium_prognosis",
            "premium_practical", "premium_conclusion", "premium_appendix"
        ]
        
        total_pages_added = 0
        
        # 1. Добавляем статические файлы в начало отчета
        block1_templates_dir = premium_templates_dir / "block-1"
        title_pdf = block1_templates_dir / "title.pdf"
        title2_pdf = block1_templates_dir / "title-2.pdf"
        
        # Создаем кастомную титульную страницу с данными пользователя
        if title_pdf.exists():
            # Получаем имя пользователя (приоритет: user.name -> "first last" -> first_name -> username -> fallback)
            if user.name:
                user_name = user.name
            elif user.first_name and user.last_name:
                user_name = f"{user.first_name} {user.last_name}"
            elif user.first_name:
                user_name = user.first_name
            elif user.username:
                user_name = user.username
            else:
                user_name = f"пользователя под {user.telegram_id}"
            
            # Форматируем дату
            completion_date = datetime.utcnow().strftime("%d.%m.%Y")
            
            # Создаем кастомную титульную страницу
            custom_title_buffer = self.pdf_generator.create_custom_title_page(title_pdf, user_name, completion_date)
            custom_title_path = temp_dir / "custom_title.pdf"
            
            with open(custom_title_path, 'wb') as f:
                f.write(custom_title_buffer.getvalue())
            temp_files.append(custom_title_path)
            
            pdf_parts.append(custom_title_path)
            total_pages_added += 1
            
        if title2_pdf.exists():
            pdf_parts.append(title2_pdf)
            total_pages_added += 1
        
        for section_key in ordered_sections:
            if section_key not in pages_by_section:
                continue
                
            # Получаем папку с шаблонами для этого блока
            block_folder = block_mapping.get(section_key)
            if not block_folder:
                print(f"⚠️ Не найдена папка шаблонов для секции {section_key}")
                continue
                
            block_templates_dir = premium_templates_dir / block_folder
            
            # Проверяем что папка существует
            if not block_templates_dir.exists():
                print(f"⚠️ Папка шаблонов не существует: {block_templates_dir}")
                continue
            
            section_pages = pages_by_section[section_key]
            section_pages.sort(key=lambda x: x[1]["page_num"])  # Сортируем по номеру страницы в секции
            
            print(f"📁 Обрабатываем блок {section_key} ({block_folder}) - {len(section_pages)} страниц")
            
            # 1. Добавляем статичный файл 1.pdf (название блока)
            block_title_pdf = block_templates_dir / "1.pdf"
            if block_title_pdf.exists():
                pdf_parts.append(block_title_pdf)
                total_pages_added += 1
                print(f"   ✅ Добавлен заголовок блока: {block_title_pdf}")
            else:
                print(f"   ⚠️ Не найден заголовок блока: {block_title_pdf}")
            
            # 2. Для каждого подблока: статичный PDF + ИИ ответ
            for i, (page_key, page_data) in enumerate(section_pages, start=1):
                page_num_in_section = page_data["page_num"]
                global_page = page_data["global_page"]
                content = page_data["content"]
                
                # Статичный PDF с описанием подблока (2.pdf, 3.pdf, 4.pdf...)
                # Используем i вместо page_num_in_section для правильной нумерации
                static_subblock_num = i + 1  # +1 потому что 1.pdf это заголовок блока
                static_subblock_pdf = block_templates_dir / f"{static_subblock_num}.pdf"
                
                if static_subblock_pdf.exists():
                    pdf_parts.append(static_subblock_pdf)
                    total_pages_added += 1
                    print(f"   ✅ Статичный подблок {static_subblock_num}: {static_subblock_pdf}")
                else:
                    print(f"   ⚠️ Не найден статичный подблок: {static_subblock_pdf}")
                
                # Генерируем динамические страницы с ответом ИИ (может быть несколько при переносе)
                print(f"   🤖 Генерируем ИИ ответ для страницы {global_page} (с автопереносом)")
                
                # Используем create_text_pages для автоматического переноса длинного текста
                print(f"   📝 Длина текста: {len(content)} символов")
                
                # Проверяем, не пустой ли контент
                if not content or not content.strip():
                    print(f"   ⚠️ Контент пустой для страницы {global_page}, пропускаем")
                    continue
                
                page_buffers = self.pdf_generator.create_text_pages(content, ai_template_path)
                
                # Обрабатываем все созданные страницы
                for page_idx, page_buffer in enumerate(page_buffers):
                    # Проверяем, не пустой ли буфер
                    if not page_buffer or page_buffer.getvalue() == b'':
                        print(f"   ⚠️ Пустой буфер для страницы {global_page}_{page_idx+1}, пропускаем")
                        continue
                    
                    if page_idx == 0:
                        # Первая страница использует исходный номер
                        ai_page_path = temp_dir / f"ai_page_{global_page:02d}_temp.pdf"
                    else:
                        # Дополнительные страницы получают суффикс
                        ai_page_path = temp_dir / f"ai_page_{global_page:02d}_{page_idx+1}_temp.pdf"
                    
                    with open(ai_page_path, 'wb') as f:
                        f.write(page_buffer.getvalue())
                    temp_files.append(ai_page_path)
                    
                    pdf_parts.append(ai_page_path)
                    total_pages_added += 1
                    
                    if page_idx == 0:
                        print(f"   ✅ ИИ ответ сохранен: {ai_page_path}")
                    else:
                        print(f"   ✅ Дополнительная страница {page_idx+1}: {ai_page_path}")
                
                if len(page_buffers) > 1:
                    print(f"   📄 Текст перенесен на {len(page_buffers)} страниц")
            
            # 3. Добавляем статичный файл note.pdf в конце блока (для заметок пользователя)
            note_pdf = block_templates_dir / "note.pdf"
            if note_pdf.exists():
                pdf_parts.append(note_pdf)
                total_pages_added += 1
                print(f"   📝 Добавлены заметки пользователя: {note_pdf}")
            else:
                print(f"   ⚠️ Не найден файл заметок: {note_pdf}")
        
        # 4. Добавляем статический файл в конец отчета
        block9_templates_dir = premium_templates_dir / "block-9"
        last_pdf = block9_templates_dir / "last.pdf"
        
        if last_pdf.exists():
            pdf_parts.append(last_pdf)
            total_pages_added += 1
        
        print(f"📊 Всего добавлено в PDF: {total_pages_added} страниц")
        return pdf_parts 