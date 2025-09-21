from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

MAIN_MENU_LAYOUT = [
    ["📥 Download"],
    ["🔍 Search", "📃 Lyrics"],
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(MAIN_MENU_LAYOUT, resize_keyboard=True)


def account_inline_keyboard(website_url: str, linked: bool) -> InlineKeyboardMarkup:
    link_btn_text = "Disconnect" if linked else "Link account"
    link_cb_data = "link:disconnect" if linked else "link:request"
    buttons = [
        [InlineKeyboardButton(link_btn_text, callback_data=link_cb_data)],
    ]
    return InlineKeyboardMarkup(buttons)
