# PDF Converter Bot

Telegram-бот и REST API для конвертации PDF файлов в различные форматы (DOCX, XLSX, PPTX, PNG, JPEG, TXT, HTML, RTF).

## Возможности

- 📤 **Загрузка PDF** через Telegram бота или REST API
- 🔄 **Конвертация** в 8+ форматов с поддержкой многостраничных документов
- ⚡ **Асинхронная обработка** через Celery + Redis
- 🔒 **Безопасность** — валидация MIME-типов, rate limiting, JWT аутентификация
- 📦 **Хранение** — MinIO (S3-compatible) с автоматической очисткой по TTL
- 🔔 **Уведомления** — об ошибках в Telegram разработчика
- 🖥️ **Web-интерфейс** — удобный React-интерфейс для работы в браузере

## Быстрый старт (локально)

### 1. Клонирование и настройка

```bash
cd "PDF converter"

# Скопируйте шаблон переменных окружения
cp .env.example .env

# Отредактируйте .env и заполните своими значениями:
# - TELEGRAM_BOT_TOKEN (от @BotFather)
# - SECRET_KEY (openssl rand -hex 32)
# - ADMIN_TELEGRAM_ID (ваш Telegram ID)
nano .env
```

### 2. Запуск через Docker Compose

```bash
# Запуск всех сервисов (backend + frontend)
docker-compose up --build

# Или через Makefile
make up
```

Сервисы будут доступны по адресам:
- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

### 3. Проверка

```bash
# Проверка здоровья API
curl http://localhost:8000/health

# Запуск проверки здоровья
./scripts/health_check.sh
```

## Деплой на VPS

### Требования

- Ubuntu 22.04 LTS
- Docker 24+
- Docker Compose 2.20+
- GitHub репозиторий с проектом

### Настройка VPS

```bash
# На сервере
mkdir -p /opt/pdf-converter
cd /opt/pdf-converter

# Клонирование репозитория
git clone https://github.com/your-username/pdf-converter.git .

# Настройка переменных окружения
cp .env.example .env
nano .env  # Заполните реальными значениями

# Запуск
docker-compose up -d --build
```

### CI/CD (GitHub Actions)

Деплой происходит автоматически при пуше в ветку `main`.

**Необходимые GitHub Secrets:**

| Secret | Описание |
|--------|----------|
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ для доступа к VPS |
| `VPS_HOST` | IP-адрес сервера |
| `VPS_USER` | SSH-пользователь (например, `deploy`) |
| `DOCKER_USERNAME` | Логин Docker Hub |
| `DOCKER_PASSWORD` | Токен Docker Hub |

## Структура проекта

```
PDF converter/
├── frontend/               # React приложение
│   ├── src/
│   │   ├── api/            # API клиент
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы приложения
│   │   ├── store/          # Zustand store
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── src/                    # Исходный код backend
│   ├── main.py             # Точка входа (FastAPI + Telegram)
│   ├── config.py           # Настройки из переменных окружения
│   ├── database.py         # Async SQLAlchemy
│   ├── models/             # SQLAlchemy модели
│   ├── api/v1/             # REST API endpoints
│   ├── services/           # Бизнес-логика
│   ├── tasks/              # Celery задачи
│   ├── handlers/           # Telegram обработчики
│   ├── middleware/         # Rate limiter, валидаторы
│   ├── schemas/            # Pydantic схемы
│   └── alembic/            # Миграции БД
├── docker/
│   ├── Dockerfile          # Backend образ
│   ├── Dockerfile.frontend # Frontend образ
│   └── nginx.conf          # Nginx конфигурация
├── scripts/
│   ├── backup.sh           # Бэкап БД
│   └── health_check.sh     # Проверка состояния
├── docker-compose.yml      # Оркестрация контейнеров
├── requirements.txt        # Python зависимости
└── .env.example            # Шаблон переменных окружения
```

## Web-интерфейс

Frontend приложение доступно по адресу http://localhost:3000 (после запуска `docker-compose up`).

### Страницы

- **Главная** (/) — информация о сервисе, поддерживаемые форматы
- **Конвертация** (/convert) — загрузка PDF и выбор формата
- **Статус** (/status/:jobId) — отслеживание прогресса конвертации
- **История** (/history) — история всех конвертаций
- **Вход/Регистрация** (/login, /register) — аутентификация

### Функции

- 📤 Drag & drop загрузка файлов
- 🎯 Выбор формата конвертации
- 📊 Прогресс-бар в реальном времени
- 📋 История конвертаций (сохраняется в браузере)
- 🔔 Уведомления об операциях

## REST API

### Основные эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/files/upload` | Загрузить PDF файл |
| GET | `/api/v1/files/download/{file_id}` | Получить ссылку на скачивание |
| POST | `/api/v1/conversions/` | Создать задачу конвертации |
| GET | `/api/v1/conversions/{job_id}` | Получить статус задачи |
| POST | `/api/v1/auth/register` | Регистрация пользователя |
| POST | `/api/v1/auth/token` | Получить JWT токен |

### Пример использования API

```bash
# 1. Регистрация
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'

# 2. Получение токена
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secret"

# 3. Загрузка файла
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"

# 4. Создание задачи конвертации
curl -X POST http://localhost:8000/api/v1/conversions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "UUID", "target_format": "docx"}'

# 5. Проверка статуса
curl http://localhost:8000/api/v1/conversions/JOB_ID
```

## Telegram бот

### Команды

- `/start` — Приветствие и описание
- `/help` — Помощь
- `/status <job_id>` — Проверка статуса задачи
- `/stats` — Статистика конвертаций (admin)
- `/cleanup` — Очистка просроченных файлов (admin)

### Использование

1. Отправьте боту PDF файл
2. Выберите формат конвертации из предложенных
3. Дождитесь завершения обработки
4. Получите готовый файл

## Поддерживаемые форматы

| Формат | Расширение | Конвертер |
|--------|------------|-----------|
| Word Document | `.docx` | Gotenberg (LibreOffice) |
| Excel Spreadsheet | `.xlsx` | Gotenberg (LibreOffice) |
| PowerPoint Presentation | `.pptx` | Gotenberg (LibreOffice) |
| Plain Text | `.txt` | PyMuPDF / OCR |
| Rich Text Format | `.rtf` | Gotenberg (LibreOffice) |
| HTML Document | `.html` | Gotenberg (LibreOffice) |
| PNG Image | `.png` | PyMuPDF |
| JPEG Image | `.jpeg` | PyMuPDF |

## Переменные окружения

Все переменные описаны в `.env.example`. Обязательные:

| Переменная | Описание |
|------------|----------|
| `SECRET_KEY` | Секретный ключ для JWT (сгенерировать: `openssl rand -hex 32`) |
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather |
| `ADMIN_TELEGRAM_ID` | Telegram ID для уведомлений об ошибках |
| `DATABASE_URL` | URL подключения к PostgreSQL |
| `REDIS_URL` | URL подключения к Redis |
| `MINIO_ACCESS_KEY` | Ключ доступа MinIO |
| `MINIO_SECRET_KEY` | Секретный ключ MinIO |

## Бэкапы

### Создание бэкапа БД

```bash
./scripts/backup.sh
```

Бэкапы сохраняются в `/opt/backups/pdf_converter/` и автоматически очищаются через 7 дней.

### Настройка cron

```bash
# Запуск каждый день в 3:00
crontab -e
0 3 * * * /opt/pdf-converter/scripts/backup.sh >> /var/log/backup.log 2>&1
```

## Мониторинг

### Проверка состояния

```bash
./scripts/health_check.sh
```

### Логи

```bash
# Backend
docker-compose logs -f pdf_bot_backend

# Celery Worker
docker-compose logs -f pdf_bot_celery_worker

# Все ошибки за последний час
docker-compose logs --tail=100 | grep -i error
```

## Устранение проблем

| Проблема | Решение |
|----------|---------|
| Ошибка миграции БД | `docker-compose exec backend alembic upgrade head` |
| Файлы не конвертируются | Проверьте логи Celery worker |
| Gotenberg недоступен | Убедитесь, что контейнер gotenberg запущен |
| Ошибка аутентификации в MinIO | Проверьте `MINIO_ACCESS_KEY` и `MINIO_SECRET_KEY` |

## Лицензия

MIT License

## Контакты

- GitHub: [your-repo]
- Telegram: [your-bot]
