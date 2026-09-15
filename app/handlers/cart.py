from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.cart import (
    cart_keyboard,
    clear_cart_confirmation_keyboard,
    empty_cart_keyboard,
)
from app.services.cart import (
    add_product,
    clear_cart,
    decrease_quantity,
    get_cart_snapshot,
    increase_quantity,
    remove_item,
)


router = Router(name="cart")


def format_price(price: int) -> str:
    return f"{price:,} تومان"


def build_cart_text(snapshot) -> str:
    if not snapshot.entries:
        return "🛒 سبد خرید شما خالی است."

    lines = ["🛒 <b>سبد خرید شما</b>", ""]

    for index, entry in enumerate(snapshot.entries, start=1):
        lines.extend(
            [
                f"{index}. <b>{escape(entry.name)}</b>",
                f"   {format_price(entry.price)} × {entry.quantity}",
                f"   جمع: {format_price(entry.subtotal)}",
            ]
        )
        if entry.issue:
            lines.append(f"   ⚠️ {escape(entry.issue)}")
        lines.append("")

    lines.append(f"💰 <b>مبلغ کل: {format_price(snapshot.total)}</b>")
    if snapshot.has_issues:
        lines.append("\n⚠️ برای ثبت سفارش ابتدا موارد نامعتبر سبد را اصلاح یا حذف کنید.")

    return "\n".join(lines)


async def show_cart_from_message(message: Message) -> None:
    if message.from_user is None:
        return

    snapshot = await get_cart_snapshot(message.from_user.id)
    markup = cart_keyboard(snapshot) if snapshot.entries else empty_cart_keyboard()

    await message.answer(
        build_cart_text(snapshot),
        parse_mode="HTML",
        reply_markup=markup,
    )


async def refresh_cart_callback(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        return

    snapshot = await get_cart_snapshot(callback.from_user.id)
    markup = cart_keyboard(snapshot) if snapshot.entries else empty_cart_keyboard()
    text = build_cart_text(snapshot)

    if callback.message.photo:
        await callback.message.delete()
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=text,
            parse_mode="HTML",
            reply_markup=markup,
        )
    else:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=markup,
        )


@router.message(F.text == "🛒 سبد خرید")
async def cart_menu_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_cart_from_message(message)


@router.callback_query(F.data == "cart:show")
async def show_cart_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await refresh_cart_callback(callback)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart_callback(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    try:
        product_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("کتاب نامعتبر است.", show_alert=True)
        return

    success, message = await add_product(
        telegram_user_id=callback.from_user.id,
        product_id=product_id,
    )
    await callback.answer(message, show_alert=not success)


@router.callback_query(F.data.startswith("cart:inc:"))
async def increase_callback(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    try:
        cart_item_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("آیتم نامعتبر است.", show_alert=True)
        return

    success, message = await increase_quantity(callback.from_user.id, cart_item_id)
    if success:
        await refresh_cart_callback(callback)
    await callback.answer(message, show_alert=not success)


@router.callback_query(F.data.startswith("cart:dec:"))
async def decrease_callback(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    try:
        cart_item_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("آیتم نامعتبر است.", show_alert=True)
        return

    success, message = await decrease_quantity(callback.from_user.id, cart_item_id)
    if success:
        await refresh_cart_callback(callback)
    await callback.answer(message, show_alert=not success)


@router.callback_query(F.data.startswith("cart:remove:"))
async def remove_callback(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    try:
        cart_item_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("آیتم نامعتبر است.", show_alert=True)
        return

    success, message = await remove_item(callback.from_user.id, cart_item_id)
    if success:
        await refresh_cart_callback(callback)
    await callback.answer(message, show_alert=not success)


@router.callback_query(F.data == "cart:clear:confirm")
async def clear_confirm_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return

    await callback.message.edit_text(
        "🗑 مطمئن هستید که می‌خواهید کل سبد خرید خالی شود؟",
        reply_markup=clear_cart_confirmation_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cart:clear:yes")
async def clear_yes_callback(callback: CallbackQuery) -> None:
    await clear_cart(callback.from_user.id)
    await refresh_cart_callback(callback)
    await callback.answer("سبد خرید خالی شد.")


@router.callback_query(F.data == "cart:clear:no")
async def clear_no_callback(callback: CallbackQuery) -> None:
    await refresh_cart_callback(callback)
    await callback.answer()


@router.callback_query(F.data == "cart:noop")
async def cart_noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()
