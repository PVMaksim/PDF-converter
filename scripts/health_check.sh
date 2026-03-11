#!/bin/bash
# Проверка состояния сервиса PDF Converter Bot
# Usage: ./health_check.sh

set -euo pipefail

echo "🏥 PDF Converter Bot — Health Check"
echo "===================================="

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local container=$2
    
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        local status=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "healthy")
        echo -e "${GREEN}✓${NC} $name: running ($status)"
        return 0
    else
        echo -e "${RED}✗${NC} $name: not running"
        return 1
    fi
}

check_port() {
    local name=$1
    local port=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name: port $port is open"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $name: port $port is not listening"
        return 1
    fi
}

# Проверка контейнеров
echo ""
echo "Контейнеры:"
check_service "PostgreSQL" "pdf_bot_db" || true
check_service "Redis" "pdf_bot_redis" || true
check_service "MinIO" "pdf_bot_minio" || true
check_service "Gotenberg" "pdf_bot_gotenberg" || true
check_service "Backend" "pdf_bot_backend" || true
check_service "Celery Worker" "pdf_bot_celery_worker" || true
check_service "Celery Beat" "pdf_bot_celery_beat" || true

# Проверка портов
echo ""
echo "Порты:"
check_port "Backend API" 8000 || true
check_port "MinIO Console" 9001 || true

# Проверка логов на ошибки
echo ""
echo "Последние ошибки в логах:"
for container in pdf_bot_backend pdf_bot_celery_worker; do
    errors=$(docker logs --tail 100 "$container" 2>/dev/null | grep -i "error\|exception\|failed" | tail -5 || true)
    if [ -n "$errors" ]; then
        echo -e "${YELLOW}⚠ ${container}:${NC}"
        echo "$errors"
    else
        echo -e "${GREEN}✓${NC} $container: no recent errors"
    fi
done

# Проверка места на диске
echo ""
echo "Место на диске:"
df -h / | tail -1

echo ""
echo "===================================="
echo "Health check completed"
