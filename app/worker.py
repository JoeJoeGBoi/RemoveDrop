import os
import subprocess
from telegram import Bot
from .config import TELEGRAM_BOT_TOKEN, BACKEND
from .processing.replicate_video import process_video as process_video_replicate
from .processing.bgremover_local import process_video as process_video_local
from .utils.logger import get_logger

log = get_logger(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def shrink_gif(in_path, max_size_mb=5):
    """Re-encode GIF until it’s ≤ max_size_mb."""
    size = os.path.getsize(in_path) / (1024 * 1024)
    if size <= max_size_mb:
        return in_path

    tmp = in_path.replace(".gif", "_small.gif")
    scale_factor = 1.0
    fps = 20

    # Gradually shrink resolution and fps until it fits
    while size > max_size_mb and scale_factor > 0.3:
        scale_factor *= 0.8
        fps = max(10, int(fps * 0.9))
        subprocess.run([
            "ffmpeg", "-y", "-i", in_path,
            "-vf", f"fps={fps},scale=iw*{scale_factor}:ih*{scale_factor}:flags=lanczos",
            "-compression_level", "9", "-loop", "0",
            tmp
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        new_size = os.path.getsize(tmp) / (1024 * 1024)
        if new_size < size:
            os.replace(tmp, in_path)
            size = new_size
        else:
            os.remove(tmp)
            break

    log.info(f"Final GIF size: {size:.2f} MB")
    return in_path


def process_and_reply(chat_id: int, status_msg_id: int, input_path: str):
    """Run background removal and send compressed GIF back to Telegram."""
    try:
        # Choose backend
        result = (
            process_video_replicate(input_path)
            if BACKEND == "replicate"
            else process_video_local(input_path)
        )

        output_url = result.get("output_url")
        local_path = result.get("output_path")

        # edit message before sending
        try:
            bot.edit_message_text(
                "Uploading your cutout… 🚀", chat_id=chat_id, message_id=status_msg_id
            )
        except Exception as e:
            log.warning(f"Failed to edit status message: {e}")

        # If we got a downloadable URL from Replicate
        if output_url:
            bot.send_animation(chat_id=chat_id, animation=output_url)
        elif local_path:
            # Ensure it’s a GIF and compress under 5 MB
            if local_path.lower().endswith(".gif"):
                local_path = shrink_gif(local_path)
            with open(local_path, "rb") as f:
                bot.send_animation(chat_id=chat_id, animation=f)

        bot.edit_message_text("Done ✅", chat_id=chat_id, message_id=status_msg_id)

    except Exception as e:
        log.exception(f"Processing failed: {e}")
        try:
            bot.edit_message_text(f"Processing failed: {e}", chat_id=chat_id, message_id=status_msg_id)
        except Exception:
            bot.send_message(chat_id=chat_id, text=f"Processing failed: {e}")
    finally:
        # Clean up temp files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if 'local_path' in locals() and local_path and os.path.exists(local_path):
                os.remove(local_path)
        except Exception as e:
            log.warning(f"Failed to remove temp file: {e}")
