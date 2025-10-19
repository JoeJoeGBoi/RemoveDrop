import os
import requests
from telegram import Bot
from .config import TELEGRAM_BOT_TOKEN
from .processing.replicate_video import process_video
from .utils.logger import get_logger

log = get_logger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def process_and_reply(chat_id: int, status_msg_id: int, input_path: str):
    try:
        result = process_video(input_path)
        output_url = result["output_url"]
        # edit status then send video
        try:
            bot.edit_message_text("Uploading your cutout… 🚀", chat_id=chat_id, message_id=status_msg_id)
        except Exception as e:
            log.warning("Failed to edit status message: %s", e)
        bot.send_video(chat_id=chat_id, video=output_url, supports_streaming=True)
        bot.edit_message_text("Done ✅", chat_id=chat_id, message_id=status_msg_id)
    except Exception as e:
        log.exception("Processing failed: %s", e)
        try:
            bot.edit_message_text(f"Processing failed: {e}", chat_id=chat_id, message_id=status_msg_id)
        except Exception:
            bot.send_message(chat_id=chat_id, text=f"Processing failed: {e}")
    finally:
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception as e:
            log.warning("Failed to remove temp file: %s", e)
