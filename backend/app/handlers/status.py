import logging
from uuid import UUID

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models import ConversionJob, JobStatus

logger = logging.getLogger(__name__)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status <job_id>  — check conversion progress.
    Usage: /status 550e8400-e29b-41d4-a716-446655440000
    """
    args = context.args
    if not args:
        await update.message.reply_text(
            "ℹ️ Usage: /status <job_id>\n"
            "Example: /status 550e8400-e29b-41d4-a716-446655440000"
        )
        return

    raw_id = args[0].strip()
    try:
        job_id = UUID(raw_id)
    except ValueError:
        await update.message.reply_text("❌ Invalid job ID format.")
        return

    async with AsyncSessionLocal() as session:
        job: ConversionJob = await session.get(ConversionJob, job_id)

    if not job:
        await update.message.reply_text("❌ Job not found.")
        return

    status_emoji = {
        JobStatus.PENDING: "⏳",
        JobStatus.PROCESSING: "⚙️",
        JobStatus.DONE: "✅",
        JobStatus.FAILED: "❌",
    }.get(job.status, "❓")

    msg_lines = [
        f"{status_emoji} Job: `{job.id}`",
        f"Status: *{job.status.value.upper()}*",
        f"Format: PDF → {job.target_format.upper()}",
        f"Created: {job.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
    ]

    if job.status == JobStatus.DONE:
        msg_lines.append("\n📥 Use /download to get your file.")
    elif job.status == JobStatus.FAILED:
        msg_lines.append(f"\nError: {job.error_message}")

    await update.message.reply_text(
        "\n".join(msg_lines),
        parse_mode="Markdown",
    )
