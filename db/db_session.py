
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import MUSIC_BOT_DB_URL

DB_URL = MUSIC_BOT_DB_URL

ENGINE_ECHO = os.getenv("SQL_ECHO", "0") == "1"
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

engine_kwargs = {
    "echo": ENGINE_ECHO,
    "future": True,
}
if DB_URL.startswith("postgresql"):
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
    })
elif DB_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })

engine = create_engine(DB_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def init_db():
    Base.metadata.create_all(engine)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
