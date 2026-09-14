from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.orders import OrderListItem


def orders_keyboard(orders: list[OrderListItem]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"سفارش #{order.order_id}",
                callback_data=f"order:view:{order.order_id}",
            )
        ]
        for order in orders
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ سفارش‌های من", callback_data="orders:list")]
        ]
    )
