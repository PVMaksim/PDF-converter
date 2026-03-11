"""
Telegram bot start and help handlers.
"""
from telegram import Update
from telegram.ext import ContextTypes

from ..config import settings


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    Sends welcome message with bot description.
    """
    user = update.effective_user
    welcome_message = f"""
👋 Привет, {user.first_name}!

Я - бот для конвертации PDF файлов в различные форматы.

📋 Доступные команды:
/start - Это сообщение
/convert - Начать конвертацию PDF
/status <job_id> - Проверить статус задачи
/help - Помощь

📤 Просто отправьте мне PDF файл, и я предложу варианты конвертации.

Поддерживаемые форматы:
• DOCX - Документы Word
• XLSX - Таблицы Excel
• PPTX - Презентации PowerPoint
• TXT - Текстовые файлы
• RTF - Rich Text Format
• PNG, JPEG - Изображения
• HTML - Веб-страницы
"""
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command.
    Sends help message with usage instructions.
    """
    help_text = f"""
🆘 Помощь по использованию бота:

1️⃣ Отправьте мне PDF файл (документом или файлом)
2️⃣ Я предложу выбрать формат для конвертации
3️⃣ После выбора начнется обработка
4️⃣ Когда файл будет готов, вы получите ссылку

⚠️ Ограничения:
• Максимальный размер файла: {settings.MAX_FILE_SIZE_FREE_MB} МБ
• Файлы хранятся: {settings.FILE_TTL_FREE_HOURS} часов
• Поддерживаются только PDF файлы

❓ Если возникли проблемы - обратитесь к администратору
"""
    await update.message.reply_text(help_text)
