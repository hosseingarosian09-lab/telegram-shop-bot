from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from aiogram.types import PhotoSize

from app.config import ROOT_DIR


UPLOAD_DIR = Path(ROOT_DIR) / "assets" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_product_photo(
    bot: Bot,
    photo: PhotoSize,
) -> str:
    filename = f"product_{uuid4().hex}.jpg"
    absolute_path = UPLOAD_DIR / filename

    await bot.download(
        photo,
        destination=absolute_path,
    )

    return f"assets/uploads/{filename}"
