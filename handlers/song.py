import asyncio
import logging
import os
from typing import List
from telegram import Update, InputFile, Message
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from utils.states import get_mode, set_mode, reset_mode, UserMode
from utils.keyboard import main_menu_keyboard
from services.youtube import get_youtube_service, TrackMeta
from services.repository import record_download


# Handlers

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_mode(context.user_data)
    await update.message.reply_text(
        "Welcome! Send a song title or YouTube link to download.",
        reply_markup=main_menu_keyboard()
    )

async def menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "📥 Download":
        set_mode(context.user_data, UserMode.DOWNLOAD)
        await update.message.reply_text("Send a song name or YouTube link.")
    elif text == "🔍 Search":
        set_mode(context.user_data, UserMode.DOWNLOAD)
        await update.message.reply_text("Send a query to search tracks.")
    elif text == "📃 Lyrics":
        await update.message.reply_text("Lyrics feature coming soon.")
    else:
        await update.message.reply_text("Unknown action.")

async def text_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    mode = get_mode(context.user_data)

    if mode in (UserMode.DOWNLOAD, UserMode.IDLE):
        await _handle_search(update, context, text)
    else:
        await update.message.reply_text("Please choose an action from the menu.")

async def _handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    if not query:
        await update.message.reply_text("Empty query.")
        return
    svc = get_youtube_service()
    searching_msg = await update.message.reply_text(f"Searching: {query} …")
    try:
        results: List[TrackMeta] = await svc.search(query, limit=1)
    except Exception:
        logging.exception("Search failed")
        await searching_msg.edit_text("Search failed. Try again later.")
        return
    if not results:
        await searching_msg.edit_text("No results.")
        return
    track_meta = results[0]
    await searching_msg.edit_text(f"Found: {track_meta.title}\nStarting download…")
    await _auto_download_and_send(update, context, track_meta, searching_msg)

async def _auto_download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, track_meta: TrackMeta, search_message: Message | None = None):
    progress_message = await update.effective_chat.send_message(f"Downloading: {track_meta.title} …")
    chat_id = progress_message.chat_id
    message_id = progress_message.message_id
    loop = asyncio.get_running_loop()

    async def _edit_progress(text: str):
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
        except Exception:
            pass

    def progress_hook(d):
        if d.get('status') == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                pct = downloaded / total * 100
                loop.call_soon_threadsafe(asyncio.create_task, _edit_progress(f"Downloading: {pct:.1f}%"))
        elif d.get('status') == 'finished':
            loop.call_soon_threadsafe(asyncio.create_task, _edit_progress("Processing audio…"))

    svc = get_youtube_service()
    try:
        file_path, final_meta = await svc.download_audio(track_meta.url, progress=progress_hook)
    except Exception:
        logging.exception("Download failed")
        await _edit_progress("Download failed.")
        return

    try:
        with open(file_path, 'rb') as f:
            audio = InputFile(f, filename=os.path.basename(file_path))
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                title=final_meta.title,
                performer=final_meta.uploader or "Unknown",
                duration=final_meta.duration or 0,
                caption=f"Source: {final_meta.url}",
            )
    except Exception:
        logging.exception("Failed sending audio")
        await _edit_progress("Failed to send audio.")
        return

    try:
        record_download(update.effective_user, final_meta)
    except Exception:
        logging.exception("DB error while saving history")

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    if search_message:
        try:
            await search_message.delete()
        except Exception:
            pass



def build_handlers():
    return [
        CommandHandler("start", cmd_start),
        MessageHandler(filters.Regex(r"^(📥 Download|🔍 Search|📃 Lyrics)$"), menu_button_handler),
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_query_handler),
    ]
