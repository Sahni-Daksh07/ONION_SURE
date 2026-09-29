"""
SQLAlchemy Database Connection and Session Management
Smart India Hackathon 2026 - Problem Statement PS26031

Requirements:
- SQLAlchemy engine with connection pooling
- Declarative Base
- FastAPI session dependency (get_db)
- Automatic rollback on exception and guaranteed cleanup
- Active connection health verification
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool, StaticPool

from .config import settings

logger = logging.getLogger(__name__)

def _build_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        eng = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        return eng

    try:
        eng = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2},
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection failed ({e}). "
            "Falling back to local SQLite database ('sqlite:///./onion_sure.db') for development."
        )
        fallback_eng = create_engine(
            "sqlite:///./onion_sure.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        @event.listens_for(fallback_eng, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        return fallback_eng


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding database session with automatic transaction management."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """Verifies live database connectivity via active query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False
