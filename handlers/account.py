import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from utils.keyboard import account_inline_keyboard
from services.repository import request_link_code, disconnect_user, get_user
# from config import WEBAPP_URL
WEBAPP_URL = "https://example.com"  # Replace with actual URL or import from config

async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    linked = bool(user and user.website_linked)
    await update.message.reply_text(
        "Account linking:",
        reply_markup=account_inline_keyboard(WEBAPP_URL, linked),
    )


async def handle_linking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "link:request":
        try:
            code = request_link_code(update.effective_user)
        except Exception:
            logging.exception("Failed to generate link code")
            await query.edit_message_text("Failed to generate code. Try again later.")
            return
        # deep_link = f"{WEBAPP_URL.rstrip('/')}/link?code={code}"
        # text = (
        #     "Your linking code: <code>{code}</code>\n"
        #     "Open the website and enter the code to complete linking.\n"
        #     "Quick link: {deep_link}"
        # ).format(code=code, deep_link=deep_link)
        text = (
            "Your linking code: <code>{code}</code>\n"
            "Open the website and enter the code to complete linking.\n"
        ).format(code=code)
        await query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=account_inline_keyboard(WEBAPP_URL, linked=False),
        )
    elif data == "link:disconnect":
        try:
            disconnect_user(update.effective_user)
        except Exception:
            logging.exception("Failed to disconnect user")
            await query.edit_message_text("Failed to disconnect. Try again later.")
            return
        await query.edit_message_text(
            text="Disconnected. You can link again anytime.",
            reply_markup=account_inline_keyboard(WEBAPP_URL, linked=False),
        )


def build_handlers():
    return [
        CommandHandler("account", cmd_account),
        CallbackQueryHandler(handle_linking_callback, pattern=r"^link:(request|disconnect)$"),
    ]

