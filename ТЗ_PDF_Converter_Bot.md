# 📄 Техническое задание: Telegram PDF Converter Bot
**Версия:** 2.0 | **Дата:** Март 2026 | **Статус:** Актуальный

---

## 1. Общее описание

Telegram-бот и веб-сервис для конвертации PDF-файлов в различные форматы с поддержкой фоновой обработки, очереди задач и масштабируемой инфраструктуры.

**Поддерживаемые форматы вывода:** DOCX, XLSX, PPTX, TXT, RTF, JPEG, PNG, HTML

> ⚠️ **Важно:** DOC, XLS, PPT (legacy-форматы) исключены из scope — они не поддерживаются современными библиотеками для генерации и несут риски совместимости. При необходимости — конвертируются из DOCX/XLSX/PPTX через LibreOffice.

---

## 2. Архитектура

### 2.1 Общая схема

```
[Telegram User] ──► [Bot Webhook] ──► [FastAPI]
                                          │
                    [Web User] ──────────►│
                                          │
                                     [Redis Queue]
                                          │
                                     [Celery Worker]
                                          │
                              ┌───────────┴──────────┐
                         [Gotenberg]            [PyMuPDF / pdfplumber]
                      (LibreOffice headless)    (текст, изображения)
                              │
                         [File Storage]
                         (MinIO / Local)
                              │
                         [PostgreSQL]
```

### 2.2 Стек технологий

#### Backend

| Компонент         | Технология                        | Обоснование                                    |
|:------------------|:----------------------------------|:-----------------------------------------------|
| Язык              | Python 3.11+                      | Поддержка async, актуальная версия             |
| Bot Framework     | `python-telegram-bot` 20.x (async)| Нативный async, активная поддержка            |
| Web Framework     | `FastAPI`                         | Async, автодокументация, типизация             |
| Task Queue        | `Celery` + `Redis`                | Фоновая обработка тяжёлых конвертаций         |
| Database          | `PostgreSQL 15+`                  | Надёжность, JSON-поля для метаданных           |
| ORM               | `SQLAlchemy 2.0` (async)          | Современный async ORM                         |
| Migrations        | `Alembic`                         | Версионирование схемы БД                      |
| Validation        | `Pydantic v2`                     | Типизация, валидация входных данных            |

#### Конвертация файлов

| Задача                       | Решение                            | Примечание                                   |
|:-----------------------------|:-----------------------------------|:---------------------------------------------|
| PDF → DOCX/XLSX/PPTX         | **Gotenberg** (Docker-сервис)      | Обёртка над LibreOffice headless, REST API   |
| PDF → текст, структура       | `pdfplumber`, `PyMuPDF (fitz)`     | Извлечение текста, таблиц, метаданных        |
| PDF → изображения            | `PyMuPDF` + `Pillow`               | Высокое качество, настройка DPI             |
| PDF → HTML                   | `pdfplumber` + шаблонизатор        | Структурированный HTML с CSS                |
| Сканы / OCR                  | `Tesseract` + `pytesseract`        | Распознавание текста на изображениях        |
| Работа с DOCX                | `python-docx`                      | Постобработка результатов конвертации       |

> 📌 **О LibreOffice headless:**
> LibreOffice headless — лучший **бесплатный** движок для конвертации Office-форматов.
> Однако напрямую управлять его процессами сложно (старт ~3–5 сек, утечки памяти при долгой работе).
> **Рекомендуется использовать через [Gotenberg](https://gotenberg.dev/)** — готовый Docker-сервис с REST API,
> который управляет пулом процессов LibreOffice, перезапускает их при падении и даёт стабильный интерфейс.
> Для **платного тарифа** можно подключить Adobe PDF Services API или Aspose Cloud — качество конвертации
> сложных документов значительно выше.

#### Frontend (Web)

| Компонент        | Технология          |
|:-----------------|:--------------------|
| Framework        | React 18+           |
| State Management | Redux Toolkit       |
| Styling          | Tailwind CSS        |
| File Upload      | react-dropzone      |
| HTTP Client      | axios               |

#### Инфраструктура

| Компонент         | Технология                  |
|:------------------|:----------------------------|
| OS                | Ubuntu 22.04 LTS            |
| Web/Proxy Server  | Nginx                       |
| App Server        | Uvicorn (behind Nginx)      |
| Containerization  | Docker + Docker Compose      |
| CI/CD             | GitHub Actions               |
| File Storage      | MinIO (self-hosted S3)       |
| Task Queue Broker | Redis 7+                    |
| Monitoring        | Prometheus + Grafana (v2.0) |

---

## 3. Структура проекта

```
PDF_Convert_Bot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Точка входа FastAPI
│   │   ├── config.py                # Pydantic Settings (env-переменные)
│   │   ├── database.py              # Async SQLAlchemy engine
│   │   ├── models/
│   │   │   ├── user.py              # Пользователи (tg_id, web, план подписки)
│   │   │   ├── conversion_job.py    # Задача конвертации (статус, прогресс, TTL)
│   │   │   └── file_record.py       # Метаданные файлов (hash, путь, размер, TTL)
│   │   ├── api/
│   │   │   ├── telegram.py          # Webhook endpoint
│   │   │   ├── conversions.py       # CRUD для задач конвертации
│   │   │   ├── files.py             # Upload / Download файлов
│   │   │   └── auth.py              # JWT-авторизация для веб
│   │   ├── services/
│   │   │   ├── converter/
│   │   │   │   ├── base.py          # Абстрактный конвертер
│   │   │   │   ├── gotenberg.py     # Конвертация через Gotenberg
│   │   │   │   ├── pymupdf.py       # Конвертация через PyMuPDF
│   │   │   │   └── ocr.py           # OCR через Tesseract
│   │   │   ├── storage.py           # MinIO / локальное хранилище
│   │   │   ├── telegram_bot.py      # Логика бота
│   │   │   └── cleanup.py           # Удаление устаревших файлов (Celery beat)
│   │   ├── tasks/
│   │   │   ├── celery_app.py        # Конфигурация Celery
│   │   │   └── convert_task.py      # Фоновая задача конвертации
│   │   ├── handlers/
│   │   │   ├── start.py
│   │   │   ├── convert.py
│   │   │   ├── status.py            # /status — прогресс конвертации
│   │   │   └── admin.py
│   │   ├── middleware/
│   │   │   ├── rate_limiter.py      # Rate limiting (slowapi)
│   │   │   └── file_validator.py    # MIME-тип, размер, безопасность
│   │   └── utils/
│   │       ├── validators.py
│   │       └── helpers.py
│   ├── alembic/                     # Миграции БД
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── requirements.txt
│   └── Dockerfile
├── gotenberg/                       # Конфиг Gotenberg-сервиса
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/                # API-клиент
│   │   ├── store/                   # Redux
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docs/
│   ├── API.md
│   ├── INSTALL.md
│   ├── DEPLOY.md
│   └── ARCHITECTURE.md
├── .github/
│   └── workflows/
│       ├── test.yml                 # Тесты на каждый PR
│       └── deploy.yml               # Deploy при мёрдже в main
├── docker-compose.yml               # Dev-окружение
├── docker-compose.prod.yml          # Prod-окружение
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Схема базы данных

### users
| Поле            | Тип           | Описание                          |
|:----------------|:--------------|:----------------------------------|
| id              | UUID PK       |                                   |
| tg_id           | BIGINT UNIQUE | Telegram user ID (null для веб)   |
| email           | VARCHAR UNIQUE| Email (null для Telegram)         |
| plan            | ENUM          | free / pro / enterprise           |
| daily_limit     | INT           | Лимит конвертаций в день          |
| created_at      | TIMESTAMP     |                                   |

### conversion_jobs
| Поле            | Тип           | Описание                                |
|:----------------|:--------------|:----------------------------------------|
| id              | UUID PK       |                                         |
| user_id         | UUID FK       |                                         |
| status          | ENUM          | pending / processing / done / failed    |
| source_format   | VARCHAR       | Всегда "pdf"                            |
| target_format   | VARCHAR       | docx / xlsx / png / ...                 |
| source_file_id  | UUID FK       | Ссылка на file_records                  |
| result_file_id  | UUID FK       | Ссылка на file_records (после готовности)|
| error_message   | TEXT          | Сообщение об ошибке                     |
| created_at      | TIMESTAMP     |                                         |
| completed_at    | TIMESTAMP     |                                         |
| expires_at      | TIMESTAMP     | TTL результирующего файла               |

### file_records
| Поле            | Тип           | Описание                         |
|:----------------|:--------------|:---------------------------------|
| id              | UUID PK       |                                  |
| storage_path    | VARCHAR       | Путь в MinIO / ФС                |
| original_name   | VARCHAR       | Оригинальное имя файла           |
| mime_type       | VARCHAR       | Проверенный MIME-тип             |
| size_bytes      | BIGINT        |                                  |
| sha256_hash     | VARCHAR       | Дедупликация                     |
| created_at      | TIMESTAMP     |                                  |
| expires_at      | TIMESTAMP     | Автоудаление через Celery beat   |

---

## 5. Безопасность

- **Валидация файлов:** проверка по MIME-типу (`python-magic`), а не только расширению
- **Лимит размера:** максимум 50 МБ (free) / 200 МБ (pro)
- **Rate limiting:** 10 конвертаций/час (free), 100/час (pro) — `slowapi`
- **Изолированная конвертация:** Gotenberg запускается в отдельном Docker-контейнере без доступа к сети
- **Хранение файлов:** временные файлы удаляются через TTL (24 ч для free, 7 дней для pro)
- **JWT-авторизация:** для веб-интерфейса
- **Переменные окружения:** все секреты только через `.env`, никогда в коде

---

## 6. Очередь задач (Celery)

Конвертация PDF — тяжёлая операция (LibreOffice: 2–15 сек, OCR: до 60 сек).
Все конвертации выполняются **асинхронно в фоне**.

**Сценарий:**
1. Пользователь отправляет файл → API принимает его, создаёт `conversion_job` со статусом `pending`, возвращает `job_id`
2. Задача попадает в очередь Redis
3. Celery Worker забирает задачу, меняет статус на `processing`
4. После завершения — статус `done`, файл сохраняется в MinIO
5. Бот / веб отправляют пользователю ссылку на скачивание

**Celery Beat (планировщик):**
- Каждые 6 часов — очистка файлов с истёкшим `expires_at`
- Раз в сутки — агрегация статистики в БД

---

## 7. Roadmap

### v1.0 — MVP (Telegram Bot)
- [ ] Базовый бот: /start, /convert, /status, /help
- [ ] Конвертация: PDF → DOCX, PDF → PNG/JPEG, PDF → TXT
- [ ] PostgreSQL + базовые модели
- [ ] Celery + Redis (фоновая обработка)
- [ ] Gotenberg (LibreOffice headless)
- [ ] Локальное хранилище файлов с TTL
- [ ] Docker Compose

### v2.0 — Web + Инфраструктура
- [ ] React веб-интерфейс (drag & drop, прогресс)
- [ ] JWT-авторизация
- [ ] MinIO вместо локального хранилища
- [ ] Расширенные форматы: XLSX, PPTX, HTML, RTF
- [ ] OCR для сканированных PDF
- [ ] Rate limiting и лимиты по тарифу
- [ ] GitHub Actions CI/CD
- [ ] Prometheus + Grafana мониторинг

### v3.0 — Монетизация + Масштаб
- [ ] Платные тарифы (Stripe / ЮKassa)
- [ ] Adobe PDF Services / Aspose (для сложных документов в pro-плане)
- [ ] Mobile App (React Native или Flutter)
- [ ] Горизонтальное масштабирование Celery Workers
- [ ] Поддержка пакетной конвертации (ZIP → ZIP)

---

## 8. Зависимости (requirements.txt)

```
# Web & Bot
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
python-telegram-bot>=20.7
pydantic-settings>=2.0.0

# Database
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0

# Task Queue
celery[redis]>=5.3.0
redis>=5.0.0

# File Processing
PyMuPDF>=1.23.0
pdfplumber>=0.10.0
python-docx>=1.1.0
openpyxl>=3.1.0
Pillow>=10.0.0
pytesseract>=0.3.10

# Security & Validation
python-magic>=0.4.27
slowapi>=0.1.9
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Storage
boto3>=1.34.0  # MinIO-совместимый клиент

# HTTP (для Gotenberg)
httpx>=0.26.0
```

---

## 9. Переменные окружения (.env.example)

```env
# App
SECRET_KEY=your-secret-key-here
DEBUG=false
ALLOWED_HOSTS=yourdomain.com

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/pdf_bot

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=pdf-converter

# Gotenberg
GOTENBERG_URL=http://gotenberg:3000

# Limits
MAX_FILE_SIZE_FREE_MB=50
MAX_FILE_SIZE_PRO_MB=200
FILE_TTL_FREE_HOURS=24
FILE_TTL_PRO_DAYS=7
```
