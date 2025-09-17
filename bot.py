import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, ContextTypes

from config import TELEGRAM_TOKEN
from db.db_session import init_db
from handlers.song import build_handlers as build_song_handlers
from handlers.account import build_handlers as build_account_handlers
from services.http_api import FlaskService

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Unhandled exception while handling update: %s", update)
    from telegram import Update as TgUpdate
    if isinstance(update, TgUpdate) and update.effective_chat:
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ An internal error occurred. Try again later.")
        except Exception:
            pass


def create_application(http_bridge: FlaskService | None = None) -> Application:
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'REPLACE_WITH_YOUR_TOKEN':
        raise RuntimeError("Telegram bot token not set")

    async def _post_init(app: Application):
        # Bind PTB's running loop to HTTP bridge for cross-thread scheduling
        if http_bridge is not None:
            http_bridge.attach_application(app)
            http_bridge.set_loop(asyncio.get_running_loop())

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(_post_init).build()
    # Register handlers
    for h in build_song_handlers():
        app.add_handler(h)
    for h in build_account_handlers():
        app.add_handler(h)
    app.add_error_handler(error_handler)
    return app

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.info("Initializing database…")
    init_db()
    logging.info("Database ready.")

    # Start lightweight HTTP bridge for website -> bot actions
    flask_host = os.getenv('FLASK_HOST', '127.0.0.1')
    flask_port = int(os.getenv('FLASK_PORT', '5001'))
    flask_api_key = os.getenv('FLASK_API_KEY')
    http_bridge = FlaskService(host=flask_host, port=flask_port, api_key=flask_api_key)
    http_bridge.start()

    app = create_application(http_bridge)

    logging.info("Starting bot polling…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        if "already running" in str(e).lower():
            loop = asyncio.get_event_loop()
            loop.create_task(create_application().initialize())
            logging.error("Detected running loop environment; consider running as standalone script.")
        else:
            raise
