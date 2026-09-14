from dataclasses import dataclass

from sqlalchemy import select

from app.database.models import CartItem, Order, OrderItem, Product
from app.database.order_repository import get_user_order_with_items, get_user_orders
from app.database.session import SessionFactory


@dataclass(frozen=True)
class CreatedOrder:
    order_id: int
    total_amount: int
    status: str


@dataclass(frozen=True)
class OrderListItem:
    order_id: int
    total_amount: int
    status: str
    created_at_text: str


@dataclass(frozen=True)
class OrderItemSnapshot:
    product_name: str
    unit_price: int
    quantity: int

    @property
    def subtotal(self) -> int:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class OrderDetails:
    order_id: int
    customer_name: str
    phone: str
    address: str
    total_amount: int
    status: str
    created_at_text: str
    items: list[OrderItemSnapshot]


def _format_created_at(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


async def create_order_from_cart(
    telegram_user_id: int,
    customer_name: str,
    phone: str,
    address: str,
) -> tuple[CreatedOrder | None, str]:
    async with SessionFactory() as session:
        async with session.begin():
            result = await session.execute(
                select(CartItem, Product)
                .join(Product, Product.id == CartItem.product_id)
                .where(CartItem.telegram_user_id == telegram_user_id)
                .order_by(CartItem.id)
            )
            rows = list(result.all())

            if not rows:
                return None, "سبد خرید شما خالی است."

            for cart_item, product in rows:
                if not product.is_active:
                    return None, f"کتاب «{product.name}» دیگر فعال نیست."

                if cart_item.quantity > product.stock:
                    return (
                        None,
                        f"موجودی «{product.name}» کافی نیست. موجودی فعلی: {product.stock}",
                    )

            total_amount = sum(
                product.price * cart_item.quantity
                for cart_item, product in rows
            )

            order = Order(
                telegram_user_id=telegram_user_id,
                customer_name=customer_name,
                phone=phone,
                address=address,
                total_amount=total_amount,
                status="pending",
            )
            session.add(order)
            await session.flush()

            for cart_item, product in rows:
                session.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=cart_item.quantity,
                    )
                )
                product.stock -= cart_item.quantity
                await session.delete(cart_item)

            order_id = order.id

        return (
            CreatedOrder(
                order_id=order_id,
                total_amount=total_amount,
                status="pending",
            ),
            "سفارش با موفقیت ثبت شد.",
        )


async def list_user_orders(telegram_user_id: int) -> list[OrderListItem]:
    async with SessionFactory() as session:
        orders = await get_user_orders(session, telegram_user_id)

    return [
        OrderListItem(
            order_id=order.id,
            total_amount=order.total_amount,
            status=order.status,
            created_at_text=_format_created_at(order.created_at),
        )
        for order in orders
    ]


async def get_order_details(
    telegram_user_id: int,
    order_id: int,
) -> OrderDetails | None:
    async with SessionFactory() as session:
        order = await get_user_order_with_items(session, telegram_user_id, order_id)

        if order is None:
            return None

        return OrderDetails(
            order_id=order.id,
            customer_name=order.customer_name,
            phone=order.phone,
            address=order.address,
            total_amount=order.total_amount,
            status=order.status,
            created_at_text=_format_created_at(order.created_at),
            items=[
                OrderItemSnapshot(
                    product_name=item.product_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                )
                for item in order.items
            ],
        )
