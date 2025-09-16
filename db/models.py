from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)  # Telegram user_id
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    website_linked = Column(Boolean, default=False)
    website_link_code = Column(Integer, nullable=False, unique=True)
    user_state = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    history = relationship("History", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

class Track(Base):
    __tablename__ = "tracks"
    __table_args__ = (
        Index("ix_tracks_created_at", "created_at"),
        Index("ix_tracks_title", "title"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=True)
    youtube_url = Column(String, nullable=False, unique=True, index=True)
    thumbnail_url = Column(String, nullable=True)
    duration = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    history = relationship("History", back_populates="track", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="track", cascade="all, delete-orphan")

class History(Base):
    __tablename__ = "history"
    __table_args__ = (
        Index("ix_history_user", "user_id"),
        Index("ix_history_track", "track_id"),
        Index("ix_history_user_time", "user_id", "downloaded_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), index=True)
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="history")
    track = relationship("Track", back_populates="history")

class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_favorites_user_track"),
        Index("ix_favorites_user", "user_id"),
        Index("ix_favorites_track", "track_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), index=True)

    user = relationship("User", back_populates="favorites")
    track = relationship("Track", back_populates="favorites")
