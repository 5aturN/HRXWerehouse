"""Асинхронное подключение к SQLite с включёнными внешними ключами и WAL."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from app.config import settings

engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.DATABASE_PATH}",
    echo=False,
    connect_args={"timeout": 15},
)

@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=5000")
    cur.close()

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    """Dependency: сессия БД на запрос."""
    async with SessionLocal() as session:
        yield session