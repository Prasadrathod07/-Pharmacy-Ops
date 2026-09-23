"""SQLAlchemy engine and session management."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def _connect_args() -> dict:
    """Enables TLS for managed MySQL hosts; local dev servers are left plain."""
    local_hosts = {"localhost", "127.0.0.1"}
    if settings.mysql_host and settings.mysql_host not in local_hosts:
        return {"ssl": {"ssl": {}}}
    return {}


engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
    connect_args=_connect_args(),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# MySQL error codes: 1205 = lock wait timeout exceeded, 1213 = deadlock found.
# Both are transient by nature (a concurrent transaction was holding/wanted
# the same row) and should surface as a 409 conflict, not an opaque 500.
_TRANSIENT_CONFLICT_ERROR_CODES = {1205, 1213}


def is_transient_conflict(exc: OperationalError) -> bool:
    orig = getattr(exc, "orig", None)
    code = orig.args[0] if orig and getattr(orig, "args", None) else None
    return code in _TRANSIENT_CONFLICT_ERROR_CODES
