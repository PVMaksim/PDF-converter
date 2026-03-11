# API Documentation

PDF Converter Bot REST API.

## Base URL

```
Development: http://localhost:8000
Production: https://yourdomain.com
```

## Authentication

Большинство эндпоинтов требуют JWT аутентификации. Токен передаётся в заголовке:

```
Authorization: Bearer <your_token>
```

## Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{"status": "ok"}
```

---

### Upload File

Загрузка PDF файла для последующей конвертации.

```http
POST /api/v1/files/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Parameters:**
- `file` (file): PDF файл (макс. 50 МБ для free, 200 МБ для pro)

**Response:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "size_bytes": 1048576,
  "duplicate": false
}
```

**Status Codes:**
- `200`: Файл успешно загружен
- `413`: Файл слишком большой
- `415`: Неверный тип файла (не PDF)
- `429`: Превышен лимит запросов

---

### Download File

Получение presigned URL для скачивания файла.

```http
GET /api/v1/files/download/{file_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "download_url": "https://minio.example.com/bucket/file.pdf?X-Amz-...",
  "filename": "document.pdf",
  "expires_in": 3600
}
```

**Status Codes:**
- `200`: URL получен
- `404`: Файл не найден
- `410`: Файл истёк (TTL)

---

### Create Conversion

Создание задачи конвертации файла.

```http
POST /api/v1/conversions/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_format": "docx"
}
```

**Response:**
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "target_format": "docx"
}
```

**Supported Formats:**
- `docx`, `xlsx`, `pptx` — Office форматы (через Gotenberg)
- `rtf`, `html` — Текстовые форматы
- `png`, `jpeg` — Изображения
- `txt` — Текст (с извлечением или OCR)

**Status Codes:**
- `200`: Задача создана
- `404`: Файл не найден
- `422`: Неподдерживаемый формат
- `429`: Превышен лимит запросов

---

### Get Job Status

Проверка статуса задачи конвертации.

```http
GET /api/v1/conversions/{job_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "done",
  "result_file_id": "770e8400-e29b-41d4-a716-446655440002",
  "error_message": null,
  "created_at": "2026-03-11T12:00:00Z",
  "completed_at": "2026-03-11T12:00:15Z"
}
```

**Job Statuses:**
- `pending` — Ожидает обработки
- `processing` — В процессе
- `done` — Завершено успешно
- `failed` — Ошибка

---

### Register User

Регистрация нового веб-пользователя.

```http
POST /api/v1/auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200`: Успешная регистрация
- `400`: Email уже зарегистрирован

---

### Login

Получение JWT токена.

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=user@example.com
password=securepassword123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200`: Успешный вход
- `401`: Неверные учётные данные

---

## Rate Limiting

API использует rate limiting для защиты от злоупотреблений.

| План | Лимит в час |
|------|-------------|
| Free | 10 запросов |
| Pro | 100 запросов |

**Response при превышении лимита:**
```json
{
  "detail": "Rate limit exceeded. Please wait before sending another request.",
  "retry_after": "3600"
}
```

---

## Error Responses

Все ошибки возвращаются в формате:

```json
{
  "detail": "Описание ошибки"
}
```

**Status Codes:**
- `400` — Неверный запрос
- `401` — Неавторизован
- `403` — Доступ запрещён
- `404` — Не найдено
- `410` — Ресурс истёк
- `413` — Файл слишком большой
- `415` — Неподдерживаемый тип
- `422` — Невалидные данные
- `429` — Превышен лимит
- `500` — Внутренняя ошибка сервера

---

## Examples

### Полный цикл конвертации (curl)

```bash
# 1. Регистрация
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}' \
  | jq -r '.access_token')

# 2. Загрузка файла
FILE_ID=$(curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" \
  | jq -r '.file_id')

# 3. Создание задачи конвертации
JOB_ID=$(curl -X POST http://localhost:8000/api/v1/conversions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\": \"$FILE_ID\", \"target_format\": \"docx\"}" \
  | jq -r '.job_id')

# 4. Ожидание завершения (polling)
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/v1/conversions/$JOB_ID" \
    -H "Authorization: Bearer $TOKEN" \
    | jq -r '.status')
  
  if [ "$STATUS" = "done" ]; then
    echo "Конвертация завершена!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Ошибка конвертации"
    break
  fi
  
  sleep 2
done

# 5. Получение ссылки на скачивание
RESULT_ID=$(curl -s "http://localhost:8000/api/v1/conversions/$JOB_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.result_file_id')

DOWNLOAD_URL=$(curl -s "http://localhost:8000/api/v1/files/download/$RESULT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.download_url')

echo "Скачать: $DOWNLOAD_URL"
```
