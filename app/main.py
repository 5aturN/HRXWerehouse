"""Точка входа. Раздает и API, и собранный фронтенд (frontend/dist)."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine
from app.models.models import Base
from app.utils.logging_conf import setup_logging
from app.routers import auth, folders, items, batches, transactions, boms, reports, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    async with engine.begin() as conn:          # создание таблиц при первом старте
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Склад-Бот", lifespan=lifespan)

for r in (auth, folders, items, batches, transactions, boms, reports, admin):
    app.include_router(r.router)

# Фронтенд: после `npm run build` файлы лежат в frontend/dist
dist = Path(__file__).parent.parent / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
