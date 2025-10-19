from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from .handlers import start, handle_media
from .utils.logger import get_logger
from .config import TELEGRAM_BOT_TOKEN

log = get_logger(__name__)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.ANIMATION, handle_media))

    log.info("Bot starting…")
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
