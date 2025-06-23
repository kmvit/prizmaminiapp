# Шрифты для PDF отчетов

Для корректного отображения кириллицы в PDF отчетах поместите TTF файлы шрифтов в эту папку.

## Рекомендуемые шрифты (в порядке приоритета):

### 1. DejaVu Sans (ЛУЧШИЙ ВЫБОР)
- **Скачать**: https://dejavu-fonts.github.io/
- **Файлы нужны**: 
  - `DejaVuSans.ttf`
  - `DejaVuSans-Bold.ttf`
- **Преимущества**: Отличная поддержка кириллицы, бесплатный, компактный

### 2. PT Sans 
- **Скачать**: https://fonts.google.com/specimen/PT+Sans
- **Файлы нужны**: 
  - `PTSans-Regular.ttf`
  - `PTSans-Bold.ttf`
- **Преимущества**: Специально разработан для кириллицы, красивый

### 3. Roboto
- **Скачать**: https://fonts.google.com/specimen/Roboto
- **Файлы нужны**: 
  - `Roboto-Regular.ttf`
  - `Roboto-Bold.ttf`
- **Преимущества**: Современный, хорошо читается

### 4. Liberation Sans
- **Скачать**: https://fonts.google.com/specimen/Liberation+Sans
- **Файлы нужны**: 
  - `LiberationSans-Regular.ttf`
  - `LiberationSans-Bold.ttf`
- **Преимущества**: Бесплатная альтернатива Arial

### 5. Open Sans
- **Скачать**: https://fonts.google.com/specimen/Open+Sans
- **Файлы нужны**: 
  - `OpenSans-Regular.ttf`
  - `OpenSans-Bold.ttf`
- **Преимущества**: Популярный веб-шрифт

## Быстрая установка DejaVu Sans:

```bash
# Скачать и распаковать DejaVu Sans
wget https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.tar.bz2
tar -xjf dejavu-fonts-ttf-2.37.tar.bz2
cp dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf ./
cp dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf ./
rm -rf dejavu-fonts-ttf-2.37*
```

## Результат:
После добавления шрифтов система автоматически их обнаружит и использует для генерации PDF с корректным отображением русского текста.

Без внешних шрифтов используются встроенные шрифты ReportLab, которые могут некорректно отображать некоторые символы кириллицы. 