import os
import logging
import asyncio
from typing import Optional
from dataclasses import dataclass
import hashlib
import requests
from PIL import Image

THUMBS_DIR = os.path.join(os.getenv("MUSIC_DOWNLOAD_DIR", "downloads"), "thumbs")
os.makedirs(THUMBS_DIR, exist_ok=True)

DEFAULT_MAX_SIZE_KB = 200
MAX_DIM = 320

@dataclass
class ThumbnailResult:
    path: str
    from_cache: bool

async def ensure_thumbnail(url: str | None, video_id: str | None, max_size_kb: int = DEFAULT_MAX_SIZE_KB) -> Optional[ThumbnailResult]:
    if not url:
        return None
    if not video_id:
        # fallback name
        video_id = hashlib.sha1(url.encode('utf-8')).hexdigest()[:16]

    out_path = os.path.join(THUMBS_DIR, f"{video_id}.jpg")
    if os.path.isfile(out_path) and os.path.getsize(out_path) <= max_size_kb * 1024:
        return ThumbnailResult(path=out_path, from_cache=True)

    def _work():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                logging.warning("Thumbnail download failed with status %s", r.status_code)
                return None
            with open(out_path, 'wb') as f:
                f.write(r.content)
            if os.path.getsize(out_path) > max_size_kb * 1024:
                _shrink_image(out_path, max_size_kb)
            return ThumbnailResult(path=out_path, from_cache=False)
        except Exception as e:
            logging.error("Thumbnail error: %s", e)
            return None
    return await asyncio.to_thread(_work)

def _shrink_image(path: str, max_size_kb: int):
    try:
        quality = 90
        while os.path.getsize(path) > max_size_kb * 1024 and quality >= 40:
            img = Image.open(path)
            img = img.convert('RGB')
            img.thumbnail((MAX_DIM, MAX_DIM))
            img.save(path, format='JPEG', optimize=True, quality=quality)
            quality -= 10
    except Exception as e:
        logging.error("Image shrink failed: %s", e)
