from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards.main_menu import HOME_BUTTON_TEXT, main_menu


router = Router(name="start")


async def _send_home(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "سلام 👋\n"
        "به فروشگاه کتاب خوش اومدی.\n"
        "از منوی زیر یک گزینه رو انتخاب کن:",
        reply_markup=main_menu,
    )


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    if message.chat.type != ChatType.PRIVATE:
        return
    await _send_home(message, state)


@router.message(F.text == HOME_BUTTON_TEXT)
async def home_button_handler(message: Message, state: FSMContext) -> None:
    if message.chat.type != ChatType.PRIVATE:
        return
    await _send_home(message, state)


@router.callback_query(F.data == "user:home")
async def home_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    if callback.message is not None:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

        await callback.message.answer(
            "🏠 منوی اصلی",
            reply_markup=main_menu,
        )

    await callback.answer()


@router.message(Command("myid"))
async def my_id_handler(message: Message) -> None:
    if message.chat.type != ChatType.PRIVATE or message.from_user is None:
        return

    admin_text = (
        "\n✅ این حساب Admin است."
        if message.from_user.id in settings.admin_ids
        else ""
    )
    await message.answer(
        f"Telegram User ID: <code>{message.from_user.id}</code>{admin_text}",
        parse_mode="HTML",
    )
