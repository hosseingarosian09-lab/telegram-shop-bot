from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import settings
from app.keyboards.admin import admin_main_keyboard
from app.keyboards.main_menu import main_menu


router = Router(name="common")


@router.message(Command("cancel"))
async def cancel_current_flow(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer(
            "فرآیند فعالی برای لغو وجود ندارد.",
            reply_markup=main_menu,
        )
        return

    await state.clear()

    is_admin_flow = current.startswith((
        "CategoryAdminStates:",
        "ProductAddStates:",
        "ProductEditStates:",
    ))
    is_admin = message.from_user is not None and message.from_user.id in settings.admin_ids

    if is_admin_flow and is_admin:
        await message.answer(
            "عملیات مدیریت لغو شد.",
            reply_markup=admin_main_keyboard(),
        )
        return

    await message.answer(
        "عملیات لغو شد. سبد خرید شما تغییری نکرد.",
        reply_markup=main_menu,
    )
