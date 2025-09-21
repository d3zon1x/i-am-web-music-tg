from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import urlparse

MAIN_MENU_LAYOUT = [
    ["📥 Download"],
    ["🔍 Search", "📃 Lyrics"],
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(MAIN_MENU_LAYOUT, resize_keyboard=True)


def account_inline_keyboard(website_url: str, linked: bool) -> InlineKeyboardMarkup:
    if linked:
        # No disconnect button anymore – only website button if public.
        buttons = []

        # If no public site, return empty keyboard (Telegram allows no buttons) – user just reads message.
        return InlineKeyboardMarkup(buttons) if buttons else InlineKeyboardMarkup([])
    # Not linked: allow requesting a code.
    buttons = [[InlineKeyboardButton("Link account", callback_data="link:request")]]

    return InlineKeyboardMarkup(buttons)
