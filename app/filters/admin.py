from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from app.config import settings


class AdminFilter(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return user is not None and user.id in settings.admin_ids
