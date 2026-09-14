from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.database.admin_repository import (
    get_latest_orders,
    get_order_any_with_items,
)
from app.database.session import SessionFactory


STATUS_LABELS = {
    "pending": "در انتظار بررسی",
    "confirmed": "تایید شده",
    "shipped": "ارسال شده",
    "completed": "تکمیل شده",
    "cancelled": "لغو شده",
}

ALLOWED_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"shipped", "cancelled"},
    "shipped": {"completed"},
    "completed": set(),
    "cancelled": set(),
}


@dataclass(frozen=True)
class AdminOrderItem:
    product_name: str
    unit_price: int
    quantity: int

    @property
    def subtotal(self) -> int:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class AdminOrder:
    order_id: int
    telegram_user_id: int
    customer_name: str
    phone: str
    address: str
    total_amount: int
    status: str
    created_at_text: str
    items: list[AdminOrderItem]


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


async def list_latest_orders(limit: int = 20) -> list[AdminOrder]:
    async with SessionFactory() as session:
        orders = await get_latest_orders(session, limit=limit)

    return [
        AdminOrder(
            order_id=order.id,
            telegram_user_id=order.telegram_user_id,
            customer_name=order.customer_name,
            phone=order.phone,
            address=order.address,
            total_amount=order.total_amount,
            status=order.status,
            created_at_text=order.created_at.strftime("%Y-%m-%d %H:%M"),
            items=[],
        )
        for order in orders
    ]


async def get_admin_order(order_id: int) -> AdminOrder | None:
    async with SessionFactory() as session:
        order = await get_order_any_with_items(session, order_id)

        if order is None:
            return None

        return AdminOrder(
            order_id=order.id,
            telegram_user_id=order.telegram_user_id,
            customer_name=order.customer_name,
            phone=order.phone,
            address=order.address,
            total_amount=order.total_amount,
            status=order.status,
            created_at_text=order.created_at.strftime("%Y-%m-%d %H:%M"),
            items=[
                AdminOrderItem(
                    product_name=item.product_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                )
                for item in order.items
            ],
        )


async def change_order_status(
    order_id: int,
    new_status: str,
) -> tuple[AdminOrder | None, str]:
    async with SessionFactory() as session:
        order = await get_order_any_with_items(session, order_id)

        if order is None:
            return None, "سفارش پیدا نشد."

        allowed = ALLOWED_TRANSITIONS.get(order.status, set())

        if new_status not in allowed:
            return None, "این تغییر وضعیت مجاز نیست."

        order.status = new_status
        await session.commit()
        await session.refresh(order)

        return (
            AdminOrder(
                order_id=order.id,
                telegram_user_id=order.telegram_user_id,
                customer_name=order.customer_name,
                phone=order.phone,
                address=order.address,
                total_amount=order.total_amount,
                status=order.status,
                created_at_text=order.created_at.strftime("%Y-%m-%d %H:%M"),
                items=[
                    AdminOrderItem(
                        product_name=item.product_name,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                    )
                    for item in order.items
                ],
            ),
            "وضعیت سفارش تغییر کرد.",
        )


async def notify_customer_status(
    bot: Bot,
    telegram_user_id: int,
    order_id: int,
    status: str,
) -> bool:
    try:
        await bot.send_message(
            chat_id=telegram_user_id,
            text=(
                f"📦 وضعیت سفارش #{order_id} تغییر کرد.\n\n"
                f"وضعیت جدید: {status_label(status)}"
            ),
        )
        return True
    except (TelegramForbiddenError, TelegramBadRequest):
        return False
