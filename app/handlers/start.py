from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import settings
from app.keyboards.main_menu import main_menu


router = Router(name="start")


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    # V1 works only in private chats.
    if message.chat.type != ChatType.PRIVATE:
        return

    user = message.from_user
    if user is None:
        return

    print(f"Telegram ID: {user.id}")
    print(f"Admin: {user.id in settings.admin_ids}")

    await message.answer(
        "سلام 👋\n"
        "به فروشگاه خوش اومدی.\n"
        "از منوی زیر یک گزینه رو انتخاب کن:",
        reply_markup=main_menu,
    )
