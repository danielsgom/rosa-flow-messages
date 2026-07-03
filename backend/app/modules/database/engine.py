from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.modules.logger import get_logger
from .models import Base

logger = get_logger(__name__)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


async def init_db(db_url: str) -> async_sessionmaker:
    """
    Initialize the async SQLAlchemy engine, create tables if they don't exist,
    and return a session factory.  Call once at application startup.
    """
    global _engine, _session_factory

    # Ensure the parent directory exists (relevant for SQLite)
    if "sqlite" in db_url:
        path_part = db_url.split("///")[-1]
        if path_part:
            resolved = Path(path_part).resolve()
            resolved.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"💾 SQLite DB path: {resolved}")

    _engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    )

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    _session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    return _session_factory


async def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
