from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def check_connection() -> dict[str, str]:
    with get_engine().connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        database = conn.execute(text("SELECT current_database()")).scalar()
        user = conn.execute(text("SELECT current_user")).scalar()
    return {
        "database": str(database or ""),
        "user": str(user or ""),
        "version": str(version or ""),
    }


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
