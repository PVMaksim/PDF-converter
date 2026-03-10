# Инструкция по деплою на сервер

## 1. Подготовка сервера

### 1.1. Настройка пользователя деплой

**На сервере (как root или sudo):**
```bash
# Создай пользователя деплой (если нет)
adduser deploy
usermod -aG sudo deploy
```

**На локальной машине:**
```bash
# Скопируй SSH-ключ на сервер
ssh-copy-id deploy@your-server-ip
```

### 1.2. Установка Docker и Docker Compose

**На сервере под пользователем deploy:**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Выйди и заново зайди под пользователем deploy
```

### 1.3. Создание директории проекта

```bash
mkdir -p /var/www/pdf-converter
cd /var/www/pdf-converter
```

---

## 2. Настройка GitHub Actions (CI/CD)

### 2.1. Создание SSH-ключа для деплоя

**На локальной машине:**
```bash
# Проверь, есть ли уже ключ
ls -la ~/.ssh/personal-ci-key*

# Если нет — создай
ssh-keygen -t ed25519 -f ~/.ssh/personal-ci-key -N ""
```

### 2.2. Добавление публичного ключа на сервер

**На локальной машине:**
```bash
# Скопируй публичный ключ на сервер
ssh-copy-id -i ~/.ssh/personal-ci-key.pub deploy@your-server-ip
```

**Или вручную:**
```bash
cat ~/.ssh/personal-ci-key.pub
# Скопируй вывод и на сервере добавь в ~/.ssh/authorized_keys
```

### 2.3. Добавление приватного ключа в GitHub Secrets

1. Открой репозиторий на GitHub
2. Settings → Secrets and variables → Actions → New secret
3. Добавь секреты:

| Name | Value |
|------|-------|
| `SSH_PRIVATE_KEY` | Содержимое файла `~/.ssh/personal-ci-key` (включая BEGIN/END) |
| `VPS_HOST` | IP-адрес сервера |
| `VPS_USER` | `deploy` |
| `DOCKER_USERNAME` | твой логин Docker Hub |
| `DOCKER_PASSWORD` | токен Docker Hub (не пароль!) |

**Как получить Docker Hub токен:**
- Docker Hub → Account Settings → Security → New Access Token

### 2.4. Создание workflow для деплоя

Создай файл `.github/workflows/deploy.yml`:

```yaml
name: Деплой на VPS

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: password
          POSTGRES_DB: pdf_bot_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s --health-timeout 5s --health-retries 5

      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r backend/requirements.txt pytest pytest-asyncio

      - name: Run unit tests
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:password@localhost:5432/pdf_bot_test
          REDIS_URL: redis://localhost:6379/0
          TELEGRAM_BOT_TOKEN: test-token
          SECRET_KEY: ci-secret-key
        run: pytest tests/unit -v

  deploy:
    runs-on: ubuntu-latest
    needs: test  # Ждём успешного завершения тестов
    steps:
      - uses: actions/checkout@v4

      - name: Сборка и пуш Docker-образа
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker build -t ${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:latest ./backend
          docker push ${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:latest

      - name: Деплой на VPS
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/pdf-converter
            docker-compose pull
            docker-compose up -d --remove-orphans
            docker image prune -f
```

---

## 3. Загрузка кода на сервер (первый раз)

### 3.1. Клонирование репозитория

**На сервере под пользователем deploy:**
```bash
cd /var/www
git clone https://github.com/your-username/pdf-converter.git
cd pdf-converter
```

### 3.2. Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

**Обязательно заполни:**
- `SECRET_KEY` — сгенерируй: `openssl rand -hex 32`
- `TELEGRAM_BOT_TOKEN` — токен от @BotFather
- `TELEGRAM_WEBHOOK_URL` — `https://твой-домен.com` (или IP)
- `DATABASE_URL` — оставь `postgresql+asyncpg://postgres:password@postgres:5432/pdf_bot` (Docker сеть)
- `MINIO_ACCESS_KEY` и `MINIO_SECRET_KEY` — измени с дефолтных `minioadmin`
- Остальные параметры при необходимости

---

## 4. Запуск проекта

### 4.1. Запуск через Docker Compose

```bash
docker-compose up -d --build
```

### 4.2. Проверка статуса

```bash
docker-compose ps
```

### 4.3. Просмотр логов

```bash
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

---

## 5. Дополнительные команды

### 5.1. Остановка проекта
```bash
docker-compose down
```

### 5.2. Перезапуск проекта
```bash
docker-compose restart
```

### 5.3. Обновление кода (ручное)

```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

### 5.4. Просмотр логов Docker
```bash
docker-compose logs -f [service]
# services: backend, celery_worker, postgres, redis, minio, gotenberg
```

### 5.5. Вход в контейнер
```bash
docker-compose exec backend bash
```

### 5.6. Очистка неиспользуемых образов
```bash
docker system prune -a
```

---

## 6. Настройка Nginx (прокси)

### 6.1. Установка Nginx
```bash
sudo apt install -y nginx
```

### 6.2. Создание конфига
```bash
sudo nano /etc/nginx/sites-available/pdf-converter
```

Добавь:
```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name твой-домен.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6.3. Активация сайта
```bash
sudo ln -s /etc/nginx/sites-available/pdf-converter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. Настройка HTTPS (Let's Encrypt)

### 7.1. Установка Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 7.2. Получение сертификата
```bash
sudo certbot --nginx -d твой-домен.com
```

### 7.3. Автоматическое обновление
```bash
sudo certbot renew --dry-run
```

---

## 8. Устранение неполадок

| Проблема | Решение |
|----------|---------|
| Контейнеры не запускаются | `docker-compose logs` |
| Нет места на диске | `df -h`, очисти логи |
| Порт 8000 занят | `sudo netstat -tulpn \| grep :8000` |
| Ошибка подключения к БД | Проверь `docker-compose ps`, жди пока postgres станет healthy |
| Миграции не применяются | `docker-compose exec backend alembic upgrade head` |

---

## 9. Бэкапы

### 9.1. Бэкап базы данных
```bash
docker-compose exec postgres pg_dump -U postgres pdf_bot > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 9.2. Бэкап файлов MinIO
```bash
docker-compose exec minio mc mirror /data /backup/minio
```

### 9.3. Восстановление из бэкапа
```bash
cat backup_20250310.sql \| docker-compose exec -T postgres psql -U postgres pdf_bot
```

---

## 10. Мониторинг

### 10.1. Статистика по контейнерам
```bash
docker stats
```

### 10.2. Проверка свободного места
```bash
df -h
docker system df
```

### 10.3. Проверка логов на ошибки
```bash
docker-compose logs --tail=100 | grep -i error
```

---

## Примечания

- **Все данные хранятся в Docker volumes:** `postgres_data`, `redis_data`, `minio_data`
- **Gotenberg** работает в изолированной сети `internal`, доступен только из backend
- **Celery worker** обрабатывает фоновые задачи конвертации
- **MinIO** — S3-совместимое хранилище для файлов
- **Telegram Bot** работает через webhook (рекомендуется HTTPS)
- Для продакшена установи `DEBUG=false` в `.env`
- Регулярно обновляй образы: `docker-compose pull && docker-compose up -d`