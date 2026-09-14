from dataclasses import dataclass

from sqlalchemy import select

from app.database.cart_repository import (
    clear_user_cart,
    delete_cart_item,
    get_cart_entries,
    get_cart_item,
    get_cart_item_by_id,
)
from app.database.models import CartItem, Product
from app.database.session import SessionFactory


@dataclass(frozen=True)
class CartEntry:
    cart_item_id: int
    product_id: int
    name: str
    price: int
    stock: int
    quantity: int

    @property
    def subtotal(self) -> int:
        return self.price * self.quantity


@dataclass(frozen=True)
class CartSnapshot:
    entries: list[CartEntry]

    @property
    def total(self) -> int:
        return sum(entry.subtotal for entry in self.entries)


async def get_cart_snapshot(telegram_user_id: int) -> CartSnapshot:
    async with SessionFactory() as session:
        rows = await get_cart_entries(session, telegram_user_id)

    return CartSnapshot(
        entries=[
            CartEntry(
                cart_item_id=cart_item.id,
                product_id=product.id,
                name=product.name,
                price=product.price,
                stock=product.stock,
                quantity=cart_item.quantity,
            )
            for cart_item, product in rows
        ]
    )


async def add_product(
    telegram_user_id: int,
    product_id: int,
) -> tuple[bool, str]:
    async with SessionFactory() as session:
        product = await session.scalar(
            select(Product).where(
                Product.id == product_id,
                Product.is_active.is_(True),
            )
        )

        if product is None:
            return False, "این کتاب پیدا نشد."

        if product.stock <= 0:
            return False, "این کتاب فعلاً ناموجود است."

        cart_item = await get_cart_item(
            session,
            telegram_user_id,
            product_id,
        )

        if cart_item is None:
            session.add(
                CartItem(
                    telegram_user_id=telegram_user_id,
                    product_id=product_id,
                    quantity=1,
                )
            )
        else:
            if cart_item.quantity >= product.stock:
                return False, "بیشتر از موجودی انبار نمی‌توان اضافه کرد."

            cart_item.quantity += 1

        await session.commit()

    return True, "به سبد خرید اضافه شد ✅"


async def increase_quantity(
    telegram_user_id: int,
    cart_item_id: int,
) -> tuple[bool, str]:
    async with SessionFactory() as session:
        cart_item = await get_cart_item_by_id(
            session,
            telegram_user_id,
            cart_item_id,
        )

        if cart_item is None:
            return False, "این آیتم دیگر در سبد وجود ندارد."

        product = await session.scalar(
            select(Product).where(
                Product.id == cart_item.product_id,
                Product.is_active.is_(True),
            )
        )

        if product is None:
            return False, "این کتاب دیگر در دسترس نیست."

        if cart_item.quantity >= product.stock:
            return False, "به حداکثر موجودی این کتاب رسیده‌اید."

        cart_item.quantity += 1
        await session.commit()

    return True, "تعداد افزایش یافت."


async def decrease_quantity(
    telegram_user_id: int,
    cart_item_id: int,
) -> tuple[bool, str]:
    async with SessionFactory() as session:
        cart_item = await get_cart_item_by_id(
            session,
            telegram_user_id,
            cart_item_id,
        )

        if cart_item is None:
            return False, "این آیتم دیگر در سبد وجود ندارد."

        if cart_item.quantity <= 1:
            return False, "حداقل تعداد ۱ است؛ برای حذف از 🗑 استفاده کنید."

        cart_item.quantity -= 1
        await session.commit()

    return True, "تعداد کاهش یافت."


async def remove_item(
    telegram_user_id: int,
    cart_item_id: int,
) -> tuple[bool, str]:
    async with SessionFactory() as session:
        cart_item = await get_cart_item_by_id(
            session,
            telegram_user_id,
            cart_item_id,
        )

        if cart_item is None:
            return False, "این آیتم دیگر در سبد وجود ندارد."

        await delete_cart_item(session, cart_item)
        await session.commit()

    return True, "از سبد حذف شد."


async def clear_cart(telegram_user_id: int) -> None:
    async with SessionFactory() as session:
        await clear_user_cart(session, telegram_user_id)
        await session.commit()
