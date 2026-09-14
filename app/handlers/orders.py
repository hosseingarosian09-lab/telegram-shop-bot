from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.orders import order_details_keyboard, orders_keyboard
from app.services.orders import get_order_details, list_user_orders


router = Router(name="orders")

STATUS_LABELS = {
    "pending": "در انتظار بررسی",
    "confirmed": "تایید شده",
    "shipped": "ارسال شده",
    "completed": "تکمیل شده",
    "cancelled": "لغو شده",
}


def format_price(price: int) -> str:
    return f"{price:,} تومان"


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


@router.message(F.text == "📦 سفارش‌های من")
async def my_orders_handler(message: Message) -> None:
    if message.from_user is None:
        return

    orders = await list_user_orders(message.from_user.id)

    if not orders:
        await message.answer("📦 هنوز سفارشی ثبت نکرده‌اید.")
        return

    lines = ["📦 <b>آخرین سفارش‌های شما</b>", ""]

    for order in orders:
        lines.extend(
            [
                f"سفارش <b>#{order.order_id}</b>",
                f"💰 {format_price(order.total_amount)}",
                f"📌 {escape(status_label(order.status))}",
                f"🕒 {escape(order.created_at_text)}",
                "",
            ]
        )

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=orders_keyboard(orders),
    )


@router.callback_query(F.data == "orders:list")
async def orders_list_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return

    orders = await list_user_orders(callback.from_user.id)

    if not orders:
        await callback.message.edit_text("📦 هنوز سفارشی ثبت نکرده‌اید.")
        await callback.answer()
        return

    lines = ["📦 <b>آخرین سفارش‌های شما</b>", ""]

    for order in orders:
        lines.extend(
            [
                f"سفارش <b>#{order.order_id}</b>",
                f"💰 {format_price(order.total_amount)}",
                f"📌 {escape(status_label(order.status))}",
                f"🕒 {escape(order.created_at_text)}",
                "",
            ]
        )

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=orders_keyboard(orders),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:view:"))
async def order_details_callback(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    try:
        order_id = int(callback.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("سفارش نامعتبر است.", show_alert=True)
        return

    order = await get_order_details(callback.from_user.id, order_id)

    if order is None:
        await callback.answer("این سفارش پیدا نشد.", show_alert=True)
        return

    lines = [
        f"📦 <b>سفارش #{order.order_id}</b>",
        f"📌 وضعیت: {escape(status_label(order.status))}",
        f"🕒 تاریخ: {escape(order.created_at_text)}",
        "",
        f"👤 {escape(order.customer_name)}",
        f"📞 {escape(order.phone)}",
        f"📍 {escape(order.address)}",
        "",
        "📚 <b>اقلام:</b>",
    ]

    for item in order.items:
        lines.append(
            f"• {escape(item.product_name)} × {item.quantity} = {format_price(item.subtotal)}"
        )

    lines.extend(["", f"💰 <b>مبلغ کل: {format_price(order.total_amount)}</b>"])

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=order_details_keyboard(),
    )
    await callback.answer()
