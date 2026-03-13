# PDF Converter Bot - Backend Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    # Для компиляции Python-пакетов
    gcc \
    g++ \
    libpq-dev \
    # Для libmagic (валидация MIME-типов)
    libmagic1 \
    # Для Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    # Для здоровья и отладки
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements сначала для лучшего кэширования
COPY requirements.txt .

# Копируем alembic конфигурацию
COPY src/alembic.ini ./alembic.ini
COPY src/alembic ./alembic

RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/

# Создаём директории для статических файлов
RUN mkdir -p src/static/uploads src/static/outputs

# Переменная окружения для Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
