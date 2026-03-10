# CLAUDE.md — Инструкции для работы с Claude над проектом

> Этот файл читает Claude в начале каждой сессии.
> Здесь — всё необходимое для быстрого погружения в проект без повторных объяснений.

---

## 🗂️ Что это за проект

**PDF Convert Bot** — Telegram-бот + веб-сервис для конвертации PDF в DOCX, XLSX, PPTX, TXT, RTF, JPEG, PNG, HTML.

**ТЗ:** `ТЗ_PDF_Converter_Bot.md` (v2.0, Март 2026)
**Текущее состояние:** см. `MEMORY.md`

---

## 🧠 Перед тем как писать код

1. **Прочитай MEMORY.md** — там актуальный статус: что сделано, что сломано, что pending
2. **Обнови MEMORY.md** в конце сессии — добавь что сделал, что не успел, новые проблемы
3. Если задача касается нескольких файлов — сначала покажи план изменений, потом пиши код

---

## ⚙️ Стек и версии

| Компонент | Технология | Версия |
|---|---|---|
| Язык | Python | 3.11+ |
| Web | FastAPI | ≥0.110 |
| Bot | python-telegram-bot | 20.x (async) |
| ORM | SQLAlchemy | 2.0 (async) |
| Migrations | Alembic | ≥1.13 |
| Validation | Pydantic | v2 |
| Queue | Celery + Redis | ≥5.3 / 7+ |
| Converter 1 | Gotenberg (Docker) | 8.x |
| Converter 2 | PyMuPDF (fitz) | ≥1.23 |
| OCR | pytesseract + Tesseract | — |
| Storage | MinIO (boto3) | S3-compatible |
| Auth | python-jose + passlib | JWT/bcrypt |
| Rate limiting | slowapi | ≥0.1.9 |
| File validation | python-magic | — |

---

## 📐 Архитектурные принципы (не нарушать)

### Асинхронность
- Весь FastAPI код — `async def`
- SQLAlchemy — только через `AsyncSession`
- Celery task (`run_conversion`) — синхронная обёртка над `asyncio.new_event_loop()` (так как Celery не async-native)
- **Никогда** не делать блокирующие I/O вызовы напрямую в async функциях — использовать `loop.run_in_executor()`

### Конвертация
- PDF → DOCX/XLSX/PPTX/RTF/HTML → только через **Gotenberg** (`services/converter/gotenberg.py`)
- PDF → PNG/JPEG/TXT → только через **PyMuPDF** (`services/converter/pymupdf.py`)
- Сканированные PDF → TXT → через **OCR** (`services/converter/ocr.py`)
- Роутинг: `get_converter(fmt)` из `services/converter/__init__.py`
- **Не использовать** `pdf2docx` — исключён в v2.0

### Хранилище
- Все файлы → **MinIO** через `services/storage.py`
- TTL реализован через поле `expires_at` в `FileRecord` + Celery beat каждые 6ч
- Локальная папка `app/static/` — только для dev-fallback, не для production

### Безопасность
- MIME проверка — `python-magic` (не расширение файла)
- Gotenberg запускается в Docker-сети `internal: true` (без интернета)
- Все секреты — только через `.env`, никогда в коде
- UUID PK везде — не раскрывать Integer ID наружу

### База данных
- Все PK — `UUID(as_uuid=True)` с `default=uuid.uuid4`
- Связи между таблицами: `users` → `conversion_jobs` → `file_records`
- Миграции — только через Alembic (`alembic upgrade head`)
- Не использовать `Base.metadata.create_all()` в production

---

## 🗃️ Структура моделей

```python
# User
id: UUID, tg_id: BigInteger (nullable), email: str (nullable),
plan: Enum(free/pro/enterprise), daily_limit: int

# FileRecord
id: UUID, storage_path: str, original_name: str, mime_type: str,
size_bytes: int, sha256_hash: str, expires_at: datetime

# ConversionJob
id: UUID, user_id: UUID→User, status: Enum(pending/processing/done/failed),
source_format: str, target_format: str,
source_file_id: UUID→FileRecord, result_file_id: UUID→FileRecord,
error_message: str, created_at, completed_at, expires_at
```

---

## 🔄 Флоу конвертации (полный путь)

```
Telegram/Web → POST /files/upload
  → validate_upload() [MIME + size]
  → MinIO upload
  → FileRecord создаётся в БД
  → возвращает file_id

→ POST /conversions/ {file_id, target_format}
  → ConversionJob создаётся (status=pending)
  → run_conversion.delay(job_id)  ← Celery task
  → возвращает job_id

→ Celery Worker:
  → скачивает PDF из MinIO
  → get_converter(fmt) → конвертирует
  → загружает результат в MinIO
  → создаёт FileRecord для результата
  → job.status = done, job.result_file_id = ...

→ GET /conversions/{job_id}  или  /status <job_id>
  → статус + result_file_id

→ GET /files/download/{file_id}
  → presigned URL из MinIO
```

---

## 🚨 Известные проблемы (актуально)

> Подробнее — в MEMORY.md раздел "🔴 Что НЕ сделано"

1. **`handlers/convert.py`** — использует старый `FileConverter` и `FileStorage` (v1). Нужно переписать под Celery + MinIO флоу
2. **`handlers/admin.py`** — использует старый `FileStorage`
3. **`handlers/start.py`** — упоминает DOC/XLS/PPT (legacy форматы не поддерживаются в v2)
4. **`schemas/conversion.py`** — Integer ID вместо UUID, устарел
5. **`alembic/env.py`** — нужно добавить импорт новых моделей
6. **`services/file_storage.py`** — старый сервис из v1, к удалению после исправления handlers
7. **`models/file_format.py`** — мёртвый код из v1, к удалению

---

## 📝 Соглашения по коду

### Именование
- Файлы модулей: `snake_case.py`
- Классы: `PascalCase`
- Функции/переменные: `snake_case`
- Константы: `UPPER_SNAKE_CASE`
- UUID в API responses: всегда `str(uuid)` — не объект

### FastAPI endpoints
- Все роуты с префиксом `/api/v1/...`
- Response model — всегда указывать явно
- Dependencies через `Depends()`:  `db: AsyncSession = Depends(get_db)`
- Текущий пользователь: `current_user: User = Depends(get_current_user)`

### Celery tasks
- Имена задач явно: `name="app.tasks.convert_task.run_conversion"`
- `bind=True` для retry-логики
- Все async операции через `_run_async(coro)` хелпер

### Логирование
```python
logger = logging.getLogger(__name__)
# INFO для бизнес-событий, DEBUG для деталей, ERROR с exc_info=True
```

### Обработка ошибок
- В конвертерах — бросать `ConversionError`
- В API — `HTTPException` с понятным `detail`
- В Celery — retry через `task.retry(exc=exc)`, обновлять `job.status = FAILED`

---

## 🐳 Docker-сервисы

| Сервис | Порт | Описание |
|---|---|---|
| `postgres` | 5432 | PostgreSQL 15 |
| `redis` | 6379 | Broker + result backend |
| `minio` | 9000 / 9001 | S3 storage / Web console |
| `gotenberg` | 3000 | LibreOffice конвертер |
| `backend` | 8000 | FastAPI + uvicorn |
| `celery_worker` | — | Воркер задач |
| `celery_beat` | — | Планировщик |

**Запуск dev:**
```bash
cp .env.example .env  # заполнить TELEGRAM_BOT_TOKEN и SECRET_KEY
docker-compose up --build
```

**Применить миграции:**
```bash
docker-compose exec backend alembic upgrade head
```

**Просмотр задач Celery:**
```bash
docker-compose exec celery_worker celery -A app.tasks.celery_app.celery_app inspect active
```

---

## 🧪 Тесты

```bash
# Unit тесты (без Docker)
cd backend && pytest tests/unit -v

# С покрытием
pytest tests/unit --cov=app --cov-report=term-missing
```

Тесты живут в `backend/tests/unit/` и `backend/tests/integration/`.
CI запускается на каждый PR через `.github/workflows/test.yml`.

---

## 🗺️ Roadmap (из ТЗ)

- **v1.0 MVP** ← сейчас (scaffold, нужно доделать handlers + первый запуск)
- **v2.0** — React frontend, JWT web auth, MinIO, OCR, расширенные форматы, CI/CD, мониторинг
- **v3.0** — монетизация (Stripe/ЮKassa), Adobe/Aspose API для pro, мобильное приложение
