# Используем стабильный образ Bookworm (Debian 12)
FROM python:3.10-bookworm

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
# В Bookworm пакеты называются так:
# - wkhtmltopdf: доступен
# - libgl1: заменяет libgl1-mesa-glx для OpenCV
# - xfonts-75dpi, xfonts-base: для рендеринга PDF
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libgl1 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python-библиотеки
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Создаем папку для данных
RUN mkdir -p /app/data

# Экспонируем порт FastAPI
EXPOSE 8000

# Команда запуска через uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
