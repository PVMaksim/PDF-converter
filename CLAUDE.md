# CLAUDE.md — PDF Converter Bot

## Стек
- Язык: Python 3.11
- Фреймворк: FastAPI + python-telegram-bot 20.x (async)
- БД: PostgreSQL 15 (asyncpg + SQLAlchemy 2.0 async)
- Очередь: Celery 5.3 + Redis 7
- Хранилище: MinIO (S3-compatible)
- Конвертация: Gotenberg 8 (LibreOffice) + PyMuPDF + Tesseract OCR
- Инфраструктура: Docker, Docker Compose, GitHub Actions, VPS (Ubuntu 22.04)

## Архитектура
Telegram-бот и REST API для конвертации PDF в DOCX, XLSX, PPTX, PNG, JPEG, TXT, HTML, RTF.
Пользователь отправляет PDF → файл валидируется → создаётся задача в БД → Celery worker обрабатывает → результат в MinIO → пользователь получает ссылку.

## Структура проекта (SKILL standard)
```
PDF converter/
├── src/                    # Исходный код приложения
│   ├── main.py             # Точка входа FastAPI + Telegram bot
│   ├── config.py           # Pydantic Settings из переменных окружения
│   ├── database.py         # Async SQLAlchemy engine + сессии
│   ├── models/             # SQLAlchemy модели (User, ConversionJob, FileRecord)
│   ├── api/                # FastAPI роутеры (v1)
│   ├── services/           # Бизнес-логика (converter, storage, telegram_bot)
│   ├── tasks/              # Celery задачи
│   ├── handlers/           # Telegram обработчики команд
│   ├── middleware/         # Rate limiter, file validator
│   ├── schemas/            # Pydantic схемы
│   └── utils/              # Вспомогательные функции
├── docker/
│   └── Dockerfile          # Образ приложения
├── tests/
│   ├── unit/               # Юнит-тесты
│   └── integration/        # Интеграционные тесты
├── scripts/
│   ├── backup.sh           # Бэкап БД
│   └── health_check.sh     # Проверка состояния
├── docs/
│   └── API.md              # API документация
├── .github/workflows/
│   ├── test.yml            # CI тесты
│   └── deploy.yml          # CD деплой
├── docker-compose.yml
├── .env.example
├── CLAUDE.md
├── MEMORY.md
└── README.md
```

## Правила написания кода
- Все функции имеют docstrings (на английском)
- Комментарии к бизнес-логике: на русском
- Никаких «магических чисел» — только именованные константы
- Всегда обрабатывать исключения через try/except с логированием
- Модульная структура: один файл = одна ответственность
- Типизация: использовать type hints для всех функций
- Конфиг загружается ТОЛЬКО из переменных окружения через Pydantic Settings

## Инструкции для ИИ (совместимость с Serena MCP)
- Держать код модульным для семантической индексации
- Чёткие, описательные имена функций и переменных (на английском)
- Документировать все публичные интерфейсы
- Избегать дублирования кода
- Приоритет: безопасность > читаемость > производительность

## Ключевые решения
- Gotenberg для Office-форматов (DOCX, XLSX, PPTX) — стабильнее прямого LibreOffice
- PyMuPDF для изображений и текста — быстрее и качественнее
- Celery для фоновой обработки — конвертация может занимать до 60 сек
- MinIO для хранения — S3-совместимость, возможность замены на AWS S3
- UUID для всех ID — безопасность, невозможность перебора
