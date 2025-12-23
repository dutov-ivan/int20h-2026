"""Database core helpers: engine creation and session factory.

This is adapted from the previous top-level `db.py`.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine

from .models import Base


def make_engine(db_url: str) -> AsyncEngine:
    return create_async_engine(db_url, echo=False, future=True)


def make_session_factory(engine: AsyncEngine):
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine):
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
