#!/bin/bash
# Резервное копирование базы данных PDF Converter Bot
# Usage: ./backup.sh [backup_dir]

set -euo pipefail

# Конфигурация
PROJECT_NAME="${PROJECT_NAME:-pdf_converter}"
BACKUP_DIR="${1:-/opt/backups/${PROJECT_NAME}}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_${DATE}.sql.gz"

# Переменные окружения для БД
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-pdf_bot}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"

# Создаём директорию для бэкапов
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting backup of ${POSTGRES_DB}..."

# Дамп базы из работающего контейнера
docker exec pdf_bot_db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$BACKUP_FILE"

# Проверяем, что файл создан
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Бэкап сохранён: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "❌ Ошибка: файл бэкапа не создан"
    exit 1
fi

# Оставляем только последние 7 дней бэкапов
echo "🧹 Удаляем старые бэкапы (старше 7 дней)..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

# Показываем список текущих бэкапов
echo "📦 Текущие бэкапы:"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "  (нет бэкапов)"

# Опционально: уведомление в Telegram
if [ -n "${BOT_TOKEN:-}" ] && [ -n "${ADMIN_TELEGRAM_ID:-}" ]; then
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -d chat_id="${ADMIN_TELEGRAM_ID}" \
      -d text="✅ Бэкап выполнен: $BACKUP_FILE ($BACKUP_SIZE)" \
      > /dev/null || true
fi

echo "✅ Backup completed successfully"
