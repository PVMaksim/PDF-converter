# MEMORY.md — Состояние проекта PDF Convert Bot

> Обновляй этот файл после каждой значимой сессии работы.
> Дата последнего обновления: **Март 2026**

---

## 📌 Текущий статус

**Версия:** v1.0 MVP (scaffold)
**Стадия:** Scaffold создан, код не запускался, тесты не прогонялись

---

## ✅ Что сделано

### Scaffold (создан в рамках перехода v1.0 → v2.0 ТЗ)

**Backend структура:**
- `app/config.py` — Pydantic Settings со всеми переменными окружения (Gotenberg, MinIO, Redis, rate limits, тарифы)
- `app/database.py` — async SQLAlchemy engine, `get_db` dependency, `init_db` / `close_db`
- `app/main.py` — FastAPI app: lifespan, CORS, slowapi, все роутеры подключены

**Модели БД (app/models/):**
- `user.py` — UUID PK, `tg_id` (BigInteger), `email`, `hashed_password`, `plan` (enum: free/pro/enterprise), `daily_limit`
- `file_record.py` — UUID PK, `storage_path`, `sha256_hash`, `expires_at` (TTL)
- `conversion_job.py` — UUID PK, FK на `users` и `file_records` (source + result), `status` (pending/processing/done/failed), `expires_at`

**API (app/api/v1/):**
- `auth.py` — JWT register/login (`/auth/register`, `/auth/token`), `get_current_user` dependency
- `files.py` — upload PDF (`/files/upload`), presigned download URL (`/files/download/{id}`)
- `conversions.py` — создать задачу (`POST /conversions/`), статус (`GET /conversions/{id}`)
- `telegram.py` — webhook endpoint (`POST /telegram/webhook`)

**Конвертеры (app/services/converter/):**
- `base.py` — абстрактный `BaseConverter`, `ConversionError`
- `gotenberg.py` — конвертация через Gotenberg REST API → DOCX, XLSX, PPTX, RTF, HTML
- `pymupdf.py` — конвертация через PyMuPDF → PNG, JPEG (ZIP для многостраничных), TXT
- `ocr.py` — OCR через pytesseract → TXT (для сканов)
- `__init__.py` — `get_converter(fmt, use_ocr)` — роутинг по формату

**Сервисы:**
- `services/storage.py` — MinIO (boto3): upload, download, delete, presigned URL, sha256
- `services/cleanup.py` — async удаление FileRecord с истёкшим `expires_at`
- `services/telegram_bot.py` — `build_application()`, `get_application()`, `set_webhook()`

**Celery (app/tasks/):**
- `celery_app.py` — конфиг + beat расписание (cleanup каждые 6ч, stats каждые сутки в 03:00 UTC)
- `convert_task.py` — `run_conversion(job_id)`: скачать из MinIO → конвертировать → загрузить → обновить job

**Middleware:**
- `middleware/file_validator.py` — проверка MIME (`python-magic`) + размера (free/pro)
- `middleware/rate_limiter.py` — slowapi лимитер по IP

**Handlers (Telegram):**
- `handlers/start.py` — `/start`, `/help` *(перенесён из старой версии, устаревшие форматы в тексте)*
- `handlers/convert.py` — обработка PDF документа, inline keyboard выбора формата, прямая конвертация *(старая логика — конвертирует синхронно через старый FileConverter, требует переписки под Celery)*
- `handlers/admin.py` — `/stats`, `/broadcast` (заглушка), `/cleanup` *(перенесён, использует старый FileStorage)*
- `handlers/status.py` — `/status <job_id>` *(новый, написан под v2.0)*

**Инфраструктура:**
- `docker-compose.yml` — postgres, redis, minio, gotenberg, backend, celery_worker, celery_beat
- `.env.example` — все переменные с комментариями
- `.gitignore`
- `alembic/versions/001_initial_migration.py` — старая схема (Integer PK, без file_records)
- `alembic/versions/002_v2_schema.py` — новая схема (UUID, file_records, планы)
- `.github/workflows/test.yml` — CI на PR/push в develop

---

## 🔴 Что НЕ сделано / требует работы

### Критично для первого запуска:

1. **handlers/convert.py** — использует старый `FileConverter` и `FileStorage` (v1 логика).
   Нужно переписать: вместо синхронной конвертации — загрузить PDF в MinIO → создать `ConversionJob` → `run_conversion.delay(job_id)` → ответить пользователю job_id и сказать "ждите"

2. **handlers/start.py** — в тексте упоминаются DOC/XLS/PPT (legacy форматы исключены из ТЗ v2.0). Нужно обновить список форматов.

3. **handlers/admin.py** — использует старый `FileStorage`. Нужно переключить на новый `storage_service` и модели v2.

4. **schemas/conversion.py** — написан под старые Integer-модели. Нужно обновить под UUID.

5. **`app/services/file_storage.py`** — старый сервис из v1, используется handlers. После переписки handlers удалить.

6. **`app/models/file_format.py`** — старая модель из v1 (таблица `file_formats`). Не используется в v2, можно удалить.

7. **`api/v1/conversions.py`** — `get_current_user` не подключён (TODO-заглушка). Нужно wiring auth.

8. **`api/v1/files.py`** — аналогично, `current_user` не инжектируется.

9. **Alembic env.py** — скорее всего ссылается на старые модели. Нужно проверить и добавить импорт новых моделей.

10. **Тесты** — только unit/test_converters.py с 3 тестами. Нет integration тестов, нет тестов для API.

### На потом (v2.0+):

- [ ] Frontend (React + Redux Toolkit + Tailwind)
- [ ] OCR auto-detection (определять скан или нет перед конвертацией)
- [ ] Дедупликация файлов по sha256 в `/files/upload`
- [ ] Webhook auto-setup при деплое
- [ ] Prometheus метрики (`/metrics`)
- [ ] `docker-compose.prod.yml` с Nginx
- [ ] `docs/` — API.md, INSTALL.md, DEPLOY.md, ARCHITECTURE.md
- [ ] `aggregate_stats_task` — реализация (сейчас заглушка)
- [ ] Ограничение `daily_limit` в `conversions.py`
- [ ] Платные тарифы (Stripe / ЮKassa) — v3.0

---

## ⚠️ Известные проблемы / решения

| Проблема | Статус | Решение |
|---|---|---|
| `handlers/convert.py` импортирует `FileStorage` которого нет в v2 | 🔴 Не исправлено | Переписать handler под Celery + MinIO |
| `models/file_format.py` — мёртвый код | 🟡 Не критично | Удалить при следующей сессии |
| `schemas/conversion.py` — Integer ID вместо UUID | 🔴 Сломает API | Обновить схемы |
| `alembic/env.py` — не импортирует новые модели | 🔴 Сломает миграции | Добавить import всех моделей в env.py |
| `start.py` упоминает DOC/XLS/PPT | 🟡 Некорректный UX | Обновить текст |
| Celery task использует sync `new_event_loop()` | 🟡 Работает но неидеально | Рассмотреть `asyncio.run()` |

---

## 🏗️ Ключевые архитектурные решения

- **Gotenberg вместо прямого LibreOffice** — изолированный Docker-сервис, управляет пулом процессов
- **Celery + Redis** — все конвертации асинхронны, FastAPI только принимает задачи
- **MinIO** — S3-совместимое хранилище, TTL реализован через `expires_at` + Celery beat
- **UUID PK везде** — безопаснее чем Integer (нельзя перебрать)
- **python-magic для MIME** — проверка по содержимому файла, не по расширению
- **Gotenberg без интернета** — `internal: true` в docker-compose сети

---

## 📁 Структура проекта (актуальная)

```
PDF_Convert_Bot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/          user, file_record, conversion_job
│   │   ├── api/v1/          auth, files, conversions, telegram
│   │   ├── services/
│   │   │   ├── converter/   base, gotenberg, pymupdf, ocr
│   │   │   ├── storage.py
│   │   │   ├── telegram_bot.py
│   │   │   └── cleanup.py
│   │   ├── tasks/           celery_app, convert_task
│   │   ├── handlers/        start*, convert*, admin*, status
│   │   ├── middleware/      file_validator, rate_limiter
│   │   ├── schemas/         conversion* (устарел)
│   │   └── utils/           helpers, validators
│   ├── alembic/
│   │   └── versions/        001 (старая), 002 (v2 схема)
│   ├── tests/unit/
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .github/workflows/test.yml
├── MEMORY.md                ← этот файл
└── CLAUDE.md
```
`*` — требует обновления/переписки

---

## 🔑 Переменные окружения (обязательные для запуска)

```env
TELEGRAM_BOT_TOKEN=        # обязательно
SECRET_KEY=                # обязательно, минимум 32 символа
DATABASE_URL=              # postgresql+asyncpg://...
```
Остальные имеют дефолты из config.py.
