import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.database.admin_repository import (
    get_latest_orders,
    get_order_any_with_items,
)
from app.database.models import Product
from app.database.session import SessionFactory


logger = logging.getLogger(__name__)

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

STATUS_ORDER = {
    "confirmed": 10,
    "shipped": 20,
    "completed": 30,
    "cancelled": 40,
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
    is_archived: bool
    created_at_text: str
    items: list[AdminOrderItem]


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def allowed_next_statuses(status: str) -> list[str]:
    return sorted(
        ALLOWED_TRANSITIONS.get(status, set()),
        key=lambda item: STATUS_ORDER.get(item, 999),
    )


def _order_view(order, include_items: bool = False) -> AdminOrder:
    return AdminOrder(
        order_id=order.id,
        telegram_user_id=order.telegram_user_id,
        customer_name=order.customer_name,
        phone=order.phone,
        address=order.address,
        total_amount=order.total_amount,
        status=order.status,
        is_archived=bool(order.is_archived),
        created_at_text=order.created_at.strftime("%Y-%m-%d %H:%M"),
        items=(
            [
                AdminOrderItem(
                    product_name=item.product_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                )
                for item in order.items
            ]
            if include_items
            else []
        ),
    )


async def list_latest_orders(
    limit: int = 20,
    archived: bool = False,
) -> list[AdminOrder]:
    async with SessionFactory() as session:
        orders = await get_latest_orders(
            session,
            limit=limit,
            archived=archived,
        )

    return [_order_view(order) for order in orders]


async def get_admin_order(order_id: int) -> AdminOrder | None:
    async with SessionFactory() as session:
        order = await get_order_any_with_items(session, order_id)
        return _order_view(order, include_items=True) if order else None


async def change_order_status(
    order_id: int,
    new_status: str,
) -> tuple[AdminOrder | None, str]:
    async with SessionFactory() as session:
        async with session.begin():
            order = await get_order_any_with_items(session, order_id)

            if order is None:
                return None, "سفارش پیدا نشد."

            if order.is_archived:
                return None, "ابتدا سفارش را از آرشیو برگردانید."

            allowed = ALLOWED_TRANSITIONS.get(order.status, set())
            if new_status not in allowed:
                return None, "این تغییر وضعیت مجاز نیست."

            if new_status == "cancelled" and not order.stock_restored:
                products_to_restore: list[tuple[Product, int]] = []
                for item in order.items:
                    product = await session.get(Product, item.product_id)
                    if product is None:
                        return (
                            None,
                            "محصولی از این سفارش پیدا نشد؛ موجودی بازیابی نشد و سفارش لغو نشد.",
                        )
                    products_to_restore.append((product, item.quantity))

                for product, quantity in products_to_restore:
                    product.stock += quantity

                order.stock_restored = True

            order.status = new_status
            await session.flush()
            result = _order_view(order, include_items=True)

        return result, "وضعیت سفارش تغییر کرد."


async def set_order_archived(
    order_id: int,
    archived: bool,
) -> tuple[AdminOrder | None, str]:
    async with SessionFactory() as session:
        order = await get_order_any_with_items(session, order_id)
        if order is None:
            return None, "سفارش پیدا نشد."

        order.is_archived = archived
        await session.commit()

        return (
            _order_view(order, include_items=True),
            "سفارش به آرشیو منتقل شد."
            if archived
            else "سفارش از آرشیو بازگردانده شد.",
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
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        logger.warning(
            "Could not notify customer about order %s status: %s",
            order_id,
            exc,
        )
        return False
