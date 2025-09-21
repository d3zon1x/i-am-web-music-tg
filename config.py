import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).parent / '.env'
if _env_path.exists():
    load_dotenv(_env_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or os.getenv('BOT_TOKEN')
if not TELEGRAM_TOKEN:
    raise RuntimeError('TELEGRAM_TOKEN not set in environment (.env)')

# Database
MUSIC_BOT_DB_URL = os.getenv('MUSIC_BOT_DB_URL')
if not MUSIC_BOT_DB_URL:
    PG_USER = os.getenv('PG_USER')
    PG_PASSWORD = os.getenv('PG_PASSWORD')
    PG_HOST = os.getenv('PG_HOST', 'localhost')
    PG_PORT = os.getenv('PG_PORT', '5432')
    PG_DB = os.getenv('PG_DB')
    if not (PG_USER and PG_PASSWORD and PG_DB):
        raise RuntimeError('Postgres variables missing: set MUSIC_BOT_DB_URL or PG_USER/PG_PASSWORD/PG_DB')
    MUSIC_BOT_DB_URL = f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'

if not MUSIC_BOT_DB_URL.startswith('postgresql'):
    raise RuntimeError('Only PostgreSQL is supported. MUSIC_BOT_DB_URL must start with postgresql')

WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8000')

# SQLAlchemy tuning
SQL_ECHO = os.getenv('SQL_ECHO', '0') == '1'
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

__all__ = [
    'TELEGRAM_TOKEN',
    'MUSIC_BOT_DB_URL',
    'SQL_ECHO',
    'DB_POOL_SIZE',
    'DB_MAX_OVERFLOW',
    'LOG_LEVEL',
    'WEBAPP_URL',
]
