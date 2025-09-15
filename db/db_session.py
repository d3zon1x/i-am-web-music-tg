# db/db_session.py
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DB_URL = os.getenv("MUSIC_BOT_DB_URL", "sqlite:///music_bot.db")

environment_opts = {}
if DB_URL.startswith("sqlite"):  # better perf pragmas optional
    environment_opts["connect_args"] = {"check_same_thread": False}

engine = create_engine(DB_URL, future=True, **environment_opts)
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

