from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # Telegram user_id
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    website_linked = Column(Boolean, default=False)
    user_state = Column(String, nullable=True)  # To track current bot interaction state
    created_at = Column(DateTime, server_default=func.now())

    history = relationship("History", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=True)
    youtube_url = Column(String, nullable=False, unique=True)
    thumbnail_url = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)  # в секундах
    created_at = Column(DateTime, server_default=func.now())

    history = relationship("History", back_populates="track", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="track", cascade="all, delete-orphan")

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"))
    downloaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="history")
    track = relationship("Track", back_populates="history")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="favorites")
    track = relationship("Track", back_populates="favorites")
