from telegram import Update
from telegram.ext import ContextTypes
from ..services.file_storage import FileStorage
import logging

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    """
    user = update.effective_user
    welcome_message = f"""
👋 Привет, {user.first_name}!

Я - бот для конвертации PDF файлов в различные форматы.

📋 Доступные команды:
/start - Это сообщение
/convert - Начать конвертацию PDF
/help - Помощь

📤 Просто отправьте мне PDF файл, и я предложу варианты конвертации.

Поддерживаемые форматы:
• DOC, DOCX - Документы Word
• XLS, XLSX - Таблицы Excel
• PPT, PPTX - Презентации PowerPoint
• TXT, RTF - Текстовые файлы
• JPEG, PNG - Изображения
• HTML - Веб-страница
"""
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command
    """
    help_text = """
🆘 Помощь по использованию бота:

1️⃣ Отправьте мне PDF файл (документом или файлом)
2️⃣ Я предложу выбрать формат для конвертации
3️⃣ После выбора начнется обработка
4️⃣ Когда файл будет готов, я пришлю вам ссылку для скачивания

⚠️ Ограничения:
• Максимальный размер файла: 50 МБ
• Файлы хранятся 24 часа
• Поддерживаются только PDF файлы

❓ Если возникли проблемы - обратитесь к администратору
"""
    await update.message.reply_text(help_text)