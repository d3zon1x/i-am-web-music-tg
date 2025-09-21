import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from utils.keyboard import account_inline_keyboard
from services.repository import request_link_code, disconnect_user, get_user
from services.link_state import register_link_message, clear_link_message
from config import WEBAPP_URL


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    linked = bool(user and user.website_linked)
    text = (
        "Account linking status:\n"
        f"{'✅ Linked' if linked else '❌ Not linked'}\n\n"+
        f'{f"Your code:\n<code>{user.website_link_code if user else 'N/A'}</code>\n\n" if linked else ""}'
    ).format(code = user.website_link_code if user else 'N/A')
    await update.message.reply_text(
        text=text,
        parse_mode="HTML",
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
        deep_link = f"{WEBAPP_URL.rstrip('/')}/link?code={code}"
        text = (
            "Your linking code:\n <code>{code}</code>\n"
            "Open the website and enter the code to complete linking.\n\n"
            "Quick link below:\n"
            # '<a href="{deep_link}">{deep_link}</a>'
        ).format(code=code)

        link_html = f'<a href="{deep_link}">{deep_link}</a>'

        try:
            new_msg1 = await query.edit_message_text(
                text=text,
                parse_mode="HTML",
            )
            await query.message.reply_text(
                text=f"{link_html}",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

            if new_msg1:  # store message reference for later success edit
                register_link_message(
                    update.effective_user.id,
                    new_msg1.chat_id,
                    new_msg1.message_id,
                )
        except Exception:
            logging.exception("Failed to edit message with code")
    elif data == "link:disconnect":
        try:
            disconnect_user(update.effective_user)
            clear_link_message(update.effective_user.id)
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
