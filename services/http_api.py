from __future__ import annotations

import os
import threading
import logging
import asyncio
from typing import Optional, Dict, Any, Callable

from flask import Flask, request, jsonify
from telegram import InputFile
from telegram.ext import Application

from services.youtube import get_youtube_service, TrackMeta
from services.media import ensure_thumbnail
from services.repository import record_download, get_user_by_link_code, mark_user_linked_by_code


class FlaskService:
    def __init__(self, host: str = '127.0.0.1', port: int = 5001, api_key: Optional[str] = None):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.api_key = api_key or os.getenv('FLASK_API_KEY')
        self._thread: Optional[threading.Thread] = None
        self._application: Optional[Application] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._setup_routes()

    def attach_application(self, application: Application):
        self._application = application

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Inject the PTB running loop (call this from within PTB context)."""
        self._loop = loop
        logging.info("FlaskService: bound to PTB event loop %s", loop)

    def start(self, *, daemon: bool = True):
        if self._thread and self._thread.is_alive():
            logging.info("FlaskService already running on %s:%s", self.host, self.port)
            return

        def _run():
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.WARNING)
            self.app.logger.handlers = logging.getLogger('services.http_api').handlers
            self.app.run(host=self.host, port=self.port, threaded=True)

        self._thread = threading.Thread(target=_run, name="FlaskServiceThread", daemon=daemon)
        self._thread.start()
        logging.info("FlaskService listening on http://%s:%s", self.host, self.port)

    def _check_auth(self, req) -> bool:
        if not self.api_key:
            return True
        return req.headers.get('X-Api-Key') == self.api_key

    def _schedule(self, coro_factory: Callable[..., asyncio.coroutines.Coroutine], *args, **kwargs) -> bool:
        if not self._application:
            return False
        loop = self._loop
        if loop and loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(coro_factory(*args, **kwargs), loop)
            def _cb(f):
                try:
                    f.result()
                except Exception:
                    logging.exception("Scheduled task failed")
            fut.add_done_callback(_cb)
            return True
        return False

    def _setup_routes(self):
        @self.app.get('/healthz')
        def healthz():
            return jsonify({"status": "ok"})

        @self.app.post('/api/link_by_code')
        def link_by_code():
            if not self._check_auth(request):
                return jsonify({"error": "unauthorized"}), 401
            data: Dict[str, Any] = request.get_json(silent=True) or {}
            code = data.get('code')
            try:
                code = int(code)
            except Exception:
                code = None
            if not code:
                return jsonify({"error": "code required"}), 400
            ok = False
            try:
                ok = mark_user_linked_by_code(code)
            except Exception:
                logging.exception("FlaskService: link_by_code failed")
                return jsonify({"error": "internal error"}), 500
            if not ok:
                return jsonify({"error": "invalid code"}), 404
            user = get_user_by_link_code(code)
            return jsonify({"status": "linked", "user_id": user.id if user else None})

        @self.app.post('/api/send_song_by_code')
        def send_song_by_code():
            if not self._check_auth(request):
                return jsonify({"error": "unauthorized"}), 401
            data: Dict[str, Any] = request.get_json(silent=True) or {}
            code = data.get('code')
            query = (data.get('query') or '').strip()
            try:
                code = int(code)
            except Exception:
                code = None
            if not code or not query:
                return jsonify({"error": "code and query are required"}), 400
            user = get_user_by_link_code(code)
            if not user or not user.website_linked:
                return jsonify({"error": "code not linked"}), 404
            if not self._application:
                return jsonify({"error": "bot not ready"}), 503
            ok = self._schedule(self._send_song_task, user.id, query)
            if not ok:
                return jsonify({"error": "bot loop not running"}), 503
            return jsonify({"status": "scheduled", "user_id": user.id, "query": query})

        @self.app.post('/api/send_song')
        def send_song():
            if not self._check_auth(request):
                return jsonify({"error": "unauthorized"}), 401

            data: Dict[str, Any] = request.get_json(silent=True) or {}
            chat_id = data.get('chat_id')
            query = (data.get('query') or '').strip()

            if not chat_id or not query:
                return jsonify({"error": "chat_id and query are required"}), 400
            if not self._application:
                return jsonify({"error": "bot not ready"}), 503

            ok = self._schedule(self._send_song_task, chat_id, query)
            if not ok:
                return jsonify({"error": "bot loop not running"}), 503
            return jsonify({"status": "scheduled", "chat_id": chat_id, "query": query})

    async def _send_song_task(self, chat_id: int, query: str):
        msg = await self._application.bot.send_message(chat_id=chat_id, text="Download from website started. Please wait…")

        svc = get_youtube_service()
        try:
            results = await svc.search(query, limit=1)
        except Exception:
            logging.exception("FlaskService: search failed for %s", query)
            return
        if not results:
            logging.info("FlaskService: no results for %s", query)
            return
        track_meta: TrackMeta = results[0]

        file_path = svc.find_cached_file(track_meta.id)
        if not file_path:
            try:
                file_path, track_meta = await svc.download_audio(track_meta.url)
            except Exception:
                logging.exception("FlaskService: download failed for %s", track_meta.url)
                return

        thumb_path = None
        try:
            thumb_res = await ensure_thumbnail(track_meta.thumbnail, track_meta.id)
            if thumb_res:
                thumb_path = thumb_res.path
        except Exception:
            logging.exception("FlaskService: ensure_thumbnail failed for %s", track_meta.id)

        try:
            with open(file_path, 'rb') as fh:
                if thumb_path and os.path.isfile(thumb_path):
                    with open(thumb_path, 'rb') as th:
                        await self._application.bot.send_audio(
                            chat_id=chat_id,
                            audio=InputFile(fh, filename=os.path.basename(file_path)),
                            title=track_meta.title,
                            performer=track_meta.uploader or "Unknown",
                            duration=track_meta.duration or 0,
                            caption="@i_am_web_music_bot",
                            thumbnail=InputFile(th),
                        )
                else:
                    await self._application.bot.send_audio(
                        chat_id=chat_id,
                        audio=InputFile(fh, filename=os.path.basename(file_path)),
                        title=track_meta.title,
                        performer=track_meta.uploader or "Unknown",
                        duration=track_meta.duration or 0,
                        caption="@i_am_web_music_bot",
                    )
        except Exception:
            logging.exception("FlaskService: failed to send audio to chat %s", chat_id)
            return

        try:
            class _FakeTgUser:
                def __init__(self, id_: int):
                    self.id = id_
                    self.username = None
                    self.first_name = None
                    self.last_name = None
            record_download(_FakeTgUser(chat_id), track_meta)
        except Exception:
            logging.exception("FlaskService: record_download failed")

        try:
            await msg.edit_text("Downloaded from website")
        except Exception:
            logging.exception("FlaskService: failed to edit status message for chat %s", chat_id)
