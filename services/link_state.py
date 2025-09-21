
from __future__ import annotations
from typing import Dict, Tuple, Optional
from threading import RLock

# user_id -> (chat_id, message_id)
_link_messages: Dict[int, Tuple[int, int]] = {}
_lock = RLock()


def register_link_message(user_id: int, chat_id: int, message_id: int) -> None:
    with _lock:
        _link_messages[user_id] = (chat_id, message_id)


def get_link_message(user_id: int) -> Optional[Tuple[int, int]]:
    with _lock:
        return _link_messages.get(user_id)


def clear_link_message(user_id: int) -> None:
    with _lock:
        _link_messages.pop(user_id, None)

