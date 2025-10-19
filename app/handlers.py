from telegram import Update
from telegram.ext import ContextTypes
import tempfile
import os
from .utils.logger import get_logger
from .config import MAX_FILE_MB
from .queue import queue
from rq.job import Job

log = get_logger(__name__)

def _mb(bytes_: int) -> float:
    return round(bytes_ / (1024 * 1024), 2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me an MP4 or GIF and I'll remove the background. "
        "Large files may take longer. Powered by hosted video matting."
    )

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    video = message.video or message.animation
    if not video:
        await message.reply_text("Send a GIF or MP4.")
        return

    size_mb = _mb(video.file_size or 0)
    if size_mb > MAX_FILE_MB:
        await message.reply_text(f"File is {size_mb} MB. Max allowed is {MAX_FILE_MB} MB.")
        return

    tg_file = await video.get_file()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        await tg_file.download_to_drive(tmp.name)
        input_path = tmp.name

    status = await message.reply_text("Got it. Cooking your cutout… ⏳")
    chat_id = message.chat_id
    status_msg_id = status.message_id

    # Enqueue background job
    job: Job = queue.enqueue(
        "app.worker.process_and_reply",
        chat_id,
        status_msg_id,
        input_path,
        job_timeout=60*20  # 20 minutes hard cap
    )
    log.info("Enqueued job %s for chat %s", job.id, chat_id)
