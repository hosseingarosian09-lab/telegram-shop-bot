import re
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.checkout import (
    checkout_cancel_keyboard,
    checkout_cancelled_keyboard,
    checkout_failed_keyboard,
    checkout_review_keyboard,
)
from app.services.cart import get_cart_snapshot
from app.services.orders import create_order_from_cart
from app.states.checkout import CheckoutStates


router = Router(name="checkout")
PHONE_PATTERN = re.compile(r"^\+?\d{8,15}$")


def format_price(price: int) -> str:
    return f"{price:,} تومان"


def normalize_phone(value: str) -> str:
    return (
        value.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )


@router.callback_query(F.data == "cart:checkout")
async def begin_checkout(callback: CallbackQuery, state: FSMContext) -> None:
    snapshot = await get_cart_snapshot(callback.from_user.id)

    if not snapshot.entries:
        await callback.answer("سبد خرید شما خالی است.", show_alert=True)
        return

    if not snapshot.can_checkout:
        await callback.answer(
            "بعضی اقلام سبد دیگر قابل سفارش نیستند. ابتدا سبد را اصلاح کنید.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(CheckoutStates.waiting_name)

    if callback.message is not None:
        await callback.message.answer(
            "مرحله ۱ از ۳\n\nنام و نام خانوادگی گیرنده را وارد کنید:",
            reply_markup=checkout_cancel_keyboard(),
        )

    await callback.answer()


@router.message(CheckoutStates.waiting_name)
async def receive_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()

    if len(name) < 2 or len(name) > 80:
        await message.answer(
            "نام باید بین ۲ تا ۸۰ کاراکتر باشد. دوباره وارد کنید:",
            reply_markup=checkout_cancel_keyboard(),
        )
        return

    await state.update_data(customer_name=name)
    await state.set_state(CheckoutStates.waiting_phone)
    await message.answer(
        "مرحله ۲ از ۳\n\nشماره تماس را وارد کنید.\nمثال: 09123456789",
        reply_markup=checkout_cancel_keyboard(),
    )


@router.message(CheckoutStates.waiting_phone)
async def receive_phone(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text or "")

    if not PHONE_PATTERN.fullmatch(phone):
        await message.answer(
            "شماره تماس معتبر نیست. فقط یک شماره ۸ تا ۱۵ رقمی وارد کنید:",
            reply_markup=checkout_cancel_keyboard(),
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(CheckoutStates.waiting_address)
    await message.answer(
        "مرحله ۳ از ۳\n\nآدرس کامل تحویل را وارد کنید:",
        reply_markup=checkout_cancel_keyboard(),
    )


@router.message(CheckoutStates.waiting_address)
async def receive_address(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()

    if len(address) < 10 or len(address) > 500:
        await message.answer(
            "آدرس باید حداقل ۱۰ کاراکتر و حداکثر ۵۰۰ کاراکتر باشد:",
            reply_markup=checkout_cancel_keyboard(),
        )
        return

    if message.from_user is None:
        await state.clear()
        return

    snapshot = await get_cart_snapshot(message.from_user.id)
    if not snapshot.can_checkout:
        await state.clear()
        await message.answer(
            "سبد خرید در زمان تسویه تغییر کرده است. ابتدا سبد را بررسی کنید.",
            reply_markup=checkout_failed_keyboard(),
        )
        return

    await state.update_data(address=address)
    await state.set_state(CheckoutStates.confirming)
    data = await state.get_data()

    lines = [
        "✅ <b>بررسی نهایی سفارش</b>",
        "",
        f"👤 {escape(data['customer_name'])}",
        f"📞 {escape(data['phone'])}",
        f"📍 {escape(data['address'])}",
        "",
        "📚 <b>اقلام سفارش:</b>",
    ]

    for entry in snapshot.entries:
        lines.append(
            f"• {escape(entry.name)} × {entry.quantity} = {format_price(entry.subtotal)}"
        )

    lines.extend(
        [
            "",
            f"💰 <b>مبلغ کل: {format_price(snapshot.total)}</b>",
            "",
            "در این نسخه پرداخت آنلاین انجام نمی‌شود.",
        ]
    )

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=checkout_review_keyboard(),
    )


@router.callback_query(CheckoutStates.confirming, F.data == "checkout:confirm")
async def confirm_checkout(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return

    data = await state.get_data()
    await callback.message.edit_text("در حال ثبت سفارش...")

    order, result_message = await create_order_from_cart(
        telegram_user_id=callback.from_user.id,
        customer_name=data["customer_name"],
        phone=data["phone"],
        address=data["address"],
    )
    await state.clear()

    if order is None:
        await callback.message.edit_text(
            f"❌ سفارش ثبت نشد.\n\n{escape(result_message)}",
            parse_mode="HTML",
            reply_markup=checkout_failed_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "✅ <b>سفارش با موفقیت ثبت شد.</b>\n\n"
        f"شماره سفارش: <b>#{order.order_id}</b>\n"
        f"مبلغ کل: <b>{format_price(order.total_amount)}</b>\n"
        "وضعیت: <b>در انتظار بررسی</b>\n\n"
        "می‌توانید وضعیت سفارش را از «📦 سفارش‌های من» ببینید.",
        parse_mode="HTML",
    )
    await callback.answer("سفارش ثبت شد ✅")


@router.callback_query(F.data == "checkout:cancel")
async def cancel_checkout_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    if callback.message is not None:
        await callback.message.edit_text(
            "تسویه حساب لغو شد. سبد خرید شما دست‌نخورده باقی ماند.",
            reply_markup=checkout_cancelled_keyboard(),
        )

    await callback.answer()
