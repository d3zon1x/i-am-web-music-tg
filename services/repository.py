from db.db_session import get_session
from db.models import User, Track, History
from services.youtube import TrackMeta
from random import randint


def _generate_unique_link_code(session):
    while True:
        code = randint(10000000, 99999999)
        if not session.query(User).filter_by(website_link_code=code).first():
            return code


def get_or_create_user(session, tg_user) -> User:
    user = session.get(User, tg_user.id)
    if not user:
        user = User(
            id=tg_user.id,
            username=getattr(tg_user, 'username', None),
            first_name=getattr(tg_user, 'first_name', None),
            last_name=getattr(tg_user, 'last_name', None),
            website_link_code=_generate_unique_link_code(session),
        )
        session.add(user)
    return user


def get_user(tg_user_id: int) -> User | None:
    with get_session() as session:
        return session.get(User, tg_user_id)


def request_link_code(tg_user) -> int:
    with get_session() as session:
        user = get_or_create_user(session, tg_user)
        user.website_linked = False
        user.website_link_code = _generate_unique_link_code(session)
        return user.website_link_code


def disconnect_user(tg_user) -> None:
    with get_session() as session:
        user = get_or_create_user(session, tg_user)
        user.website_linked = False
        user.website_link_code = _generate_unique_link_code(session)


def get_or_create_track(session, meta: TrackMeta) -> Track:
    track = session.query(Track).filter_by(youtube_url=meta.url).first()
    if not track:
        track = Track(
            title=meta.title,
            artist=meta.uploader,
            youtube_url=meta.url,
            thumbnail_url=meta.thumbnail,
            duration=meta.duration,
        )
        session.add(track)
    return track


def add_history(session, user: User, track: Track) -> History:
    history = History(user=user, track=track)
    session.add(history)
    return history


def record_download(tg_user, track_meta: TrackMeta) -> None:
    with get_session() as session:
        user = get_or_create_user(session, tg_user)
        track = get_or_create_track(session, track_meta)
        add_history(session, user, track)


def get_user_by_link_code(code: int) -> User | None:
    with get_session() as session:
        return session.query(User).filter(User.website_link_code == code).first()


def mark_user_linked_by_code(code: int) -> bool:
    with get_session() as session:
        user = session.query(User).filter(User.website_link_code == code).first()
        if not user:
            return False
        user.website_linked = True
        return True
