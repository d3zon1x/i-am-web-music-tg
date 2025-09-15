import asyncio
import re
import os
import uuid
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable, Dict, Any
import yt_dlp

YDL_AUDIO_OPTS_BASE = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "nocheckcertificate": True,
    "skip_download": True,
}

DOWNLOAD_DIR = os.getenv("MUSIC_DOWNLOAD_DIR", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YT_URL_RE = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/")

@dataclass
class TrackMeta:
    id: str
    title: str
    url: str
    duration: int | None
    uploader: str | None
    thumbnail: str | None
    source: str = "youtube"

    def to_dict(self):
        return asdict(self)

class YouTubeService:
    def __init__(self):
        pass

    @staticmethod
    def _build_search_query(query: str, limit: int) -> str:
        if YouTubeService.is_url(query):
            return query
        return f"ytsearch{limit}:{query}" if limit > 1 else f"ytsearch:{query}"

    @staticmethod
    def is_url(text: str) -> bool:
        return bool(YT_URL_RE.match(text.strip()))

    @staticmethod
    def normalize_url(url: str) -> str:
        return url.strip()

    @staticmethod
    def cached_path_for(track_id: str) -> str:
        return os.path.join(DOWNLOAD_DIR, f"{track_id}.mp3")

    @staticmethod
    def find_cached_file(track_id: str) -> str | None:
        if not track_id:
            return None
        path = YouTubeService.cached_path_for(track_id)
        if os.path.isfile(path):
            return path
        # fallback: legacy pattern search (title-random.mp3) not deterministic; skip for now
        # Could implement glob search if needed
        return None

    async def search(self, query: str, limit: int = 5) -> List[TrackMeta]:
        search_q = self._build_search_query(query, limit)
        def _extract():
            opts = {**YDL_AUDIO_OPTS_BASE}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_q, download=False)
                entries = info.get('entries') if 'entries' in info else [info]
                results: List[TrackMeta] = []
                for e in entries[:limit]:
                    results.append(TrackMeta(
                        id=e.get('id'),
                        title=e.get('title'),
                        url=e.get('webpage_url') or e.get('url') or '',
                        duration=e.get('duration'),
                        uploader=e.get('uploader'),
                        thumbnail=e.get('thumbnail'),
                    ))
                return results
        return await asyncio.to_thread(_extract)

    async def download_audio(self, url: str, *, progress: Optional[Callable[[Dict[str, Any]], None]] = None) -> tuple[str, TrackMeta]:
        safe_url = self.normalize_url(url)
        tmp_id = uuid.uuid4().hex
        def hook(d):
            if progress:
                progress(d)
        def _download():
            opts = {
                **YDL_AUDIO_OPTS_BASE,
                'skip_download': False,
                # deterministic filename: id.ext (yt-dlp will substitute id)
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [hook],
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(safe_url, download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                final_path = self.cached_path_for(info.get('id')) if info.get('id') else ydl.prepare_filename(info)
                if not final_path.endswith('.mp3'):
                    # ensure mp3 extension
                    base = os.path.splitext(final_path)[0]
                    final_path = base + '.mp3'
                meta = TrackMeta(
                    id=info.get('id'),
                    title=info.get('title'),
                    url=info.get('webpage_url') or safe_url,
                    duration=info.get('duration'),
                    uploader=info.get('uploader'),
                    thumbnail=info.get('thumbnail'),
                )
                return final_path, meta
        return await asyncio.to_thread(_download)

_youtube_service: YouTubeService | None = None

def get_youtube_service() -> YouTubeService:
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service
