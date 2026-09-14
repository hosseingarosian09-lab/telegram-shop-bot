from pathlib import Path

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import ROOT_DIR


DATA_DIR = Path(ROOT_DIR) / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATA_DIR / "shop.db"
DATABASE_URL = URL.create("sqlite+aiosqlite", database=str(DATABASE_PATH))

engine = create_async_engine(DATABASE_URL, echo=False)
SessionFactory = async_sessionmaker(bind=engine, expire_on_commit=False)
