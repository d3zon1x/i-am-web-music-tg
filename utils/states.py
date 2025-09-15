
from enum import Enum

class UserMode(str, Enum):
    IDLE = "idle"
    DOWNLOAD = "download"

STATE_KEY = "mode"

def set_mode(user_data: dict, mode: UserMode):
    user_data[STATE_KEY] = mode.value

def get_mode(user_data: dict) -> UserMode:
    raw = user_data.get(STATE_KEY, UserMode.IDLE.value)
    try:
        return UserMode(raw)
    except ValueError:
        return UserMode.IDLE

def reset_mode(user_data: dict):
    user_data[STATE_KEY] = UserMode.IDLE.value

