
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

MAIN_MENU_LAYOUT = [
    ["📥 Download"],
    ["🔍 Search", "📃 Lyrics"],
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(MAIN_MENU_LAYOUT, resize_keyboard=True)



