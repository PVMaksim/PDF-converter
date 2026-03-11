# MEMORY.md — PDF Converter Bot

## Последняя сессия: 11 марта 2026
### Сделано
- ✅ Анализ проекта — найдено 15+ проблем
- ✅ Создана новая структура по стандарту SKILL (src/, docker/, scripts/)
- ✅ Обновлён CLAUDE.md
- ✅ Исправлен config.py — добавлены ADMIN_TELEGRAM_ID, USE_LOCAL_STORAGE
- ✅ Исправлен database.py — корректный get_db() с rollback/commit
- ✅ Создан utils/error_notifier.py — уведомления об ошибках в Telegram
- ✅ Обновлён main.py — глобальный exception handler с уведомлениями
- ✅ Создан docker/Dockerfile — с Tesseract, libmagic, правильным CMD
- ✅ Обновлён docker-compose.yml — изолированные сети, health checks, logging
- ✅ Создан scripts/backup.sh — бэкап БД с очисткой старых файлов
- ✅ Создан scripts/health_check.sh — проверка состояния сервисов
- ✅ Обновлён .env.example — подробные комментарии
- ✅ Исправлены модели данных — UUID, индексы, relationships
- ✅ Обновлён middleware/rate_limiter.py — динамические лимиты
- ✅ Обновлён middleware/file_validator.py — валидация MIME и размера
- ✅ Обновлён api/v1/auth.py — JWT аутентификация
- ✅ Обновлён api/v1/files.py — rate limiting, дедупликация файлов
- ✅ Обновлён api/v1/conversions.py — auth dependency, rate limiting
- ✅ Переписан handlers/convert.py — устранён конфликтующий код
- ✅ Обновлены handlers (start, status, admin) — актуальные импорты
- ✅ Обновлён services/telegram_bot.py — callback query handler
- ✅ Обновлён services/storage.py — fallback на локальное хранилище
- ✅ Обновлены converter services (base, gotenberg, pymupdf, ocr) — docstrings
- ✅ Обновлён services/cleanup.py — удаление просроченных файлов
- ✅ Обновлены tasks (celery_app, convert_task) — уведомления об ошибках
- ✅ Создана миграция 001_initial_migration.py — UUID схема с нуля
- ✅ Обновлён alembic/env.py — правильная структура
- ✅ Создан requirements.txt — актуальные зависимости
- ✅ Создан README.md — полная документация
- ✅ Создан docs/API.md — API документация с примерами
- ✅ Обновлены .github/workflows (test.yml, deploy.yml) — правильная структура
- ✅ Созданы тесты (unit + integration) — converters, config, middleware, API
- ✅ Создан pytest.ini, conftest.py — настройка тестирования
- ✅ Создан .dockerignore — исключение лишних файлов

### Проблемы / Баги (исправленные)
- ✅ Миграции БД — создана новая схема с UUID
- ✅ handlers/convert.py — переписан с нуля
- ✅ Нет аутентификации в API — реализована через JWT
- ✅ Rate limiting не применялся — добавлены декораторы @limiter.limit
- ✅ Хардкод паролей в docker-compose.yml — заменено на переменные
- ✅ Dockerfile не соответствовал структуре — исправлен путь CMD
- ✅ Нет Tesseract для OCR — добавлен в Dockerfile
- ✅ database.py — исправлен get_db() с proper rollback
- ✅ Нет fallback для MinIO — реализован USE_LOCAL_STORAGE
- ✅ Нет уведомлений об ошибках — создан error_notifier.py

### Принятые решения
- Перейти на структуру SKILL для единообразия проектов
- Сохранить архитектуру (FastAPI + Celery + Gotenberg)
- Добавить уведомления об ошибках в Telegram
- Реализовать proper auth dependency injection
- Использовать UUID для всех ID
- Добавить fallback на локальное хранилище для разработки
- Tesseract OCR требует установки в Docker образ

## Следующая сессия
- [ ] Протестировать запуск через docker-compose up --build
- [ ] Проверить миграции БД (alembic upgrade head)
- [ ] Протестировать Telegram бота
- [ ] Протестировать API endpoints через /docs
- [ ] Проверить Celery worker + beat
- [ ] Настроить HTTPS (Certbot) для production
- [ ] Добавить frontend (React) при необходимости

## Известный технический долг
- Frontend (React) отсутствует — не в приоритете
- Мониторинг (Prometheus + Grafana) не настроен
- Интеграционные тесты требуют доработки (mock внешних сервисов)
- Статистика агрегация (aggregate_stats_task) — не реализована
- Пакетная конвертация (ZIP → ZIP) — в roadmap v3.0

## Файлы для удаления (старая структура)
- backend/ — можно удалить после тестирования
- backend/alembic/ — перенесено в src/alembic/
- old_alembic/ — если создавался
