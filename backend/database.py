"""Database configuration.

The app stores its data in a single SQLite file. By default it lives in
data/portfolio.db in the project root. To use a different file, set the
DATABASE_PATH environment variable before starting the app.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "portfolio.db"

_db_path = Path(os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH))


def configure(path):
    """Point the app at a different database file (used by the tests)."""
    global _db_path
    _db_path = Path(path)


def get_db_path():
    return _db_path


@contextmanager
def connection():
    """Open a connection, commit on success, roll back on error, always close.

    The ORM opens one of these for every operation, so no connection is left
    open between requests.
    """
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
