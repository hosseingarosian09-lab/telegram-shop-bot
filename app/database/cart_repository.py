from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CartItem, Category, Product


async def get_cart_item(
    session: AsyncSession,
    telegram_user_id: int,
    product_id: int,
) -> CartItem | None:
    return await session.scalar(
        select(CartItem).where(
            CartItem.telegram_user_id == telegram_user_id,
            CartItem.product_id == product_id,
        )
    )


async def get_cart_item_by_id(
    session: AsyncSession,
    telegram_user_id: int,
    cart_item_id: int,
) -> CartItem | None:
    return await session.scalar(
        select(CartItem).where(
            CartItem.id == cart_item_id,
            CartItem.telegram_user_id == telegram_user_id,
        )
    )


async def get_cart_entries(
    session: AsyncSession,
    telegram_user_id: int,
) -> list[tuple[CartItem, Product, Category]]:
    result = await session.execute(
        select(CartItem, Product, Category)
        .join(Product, Product.id == CartItem.product_id)
        .join(Category, Category.id == Product.category_id)
        .where(CartItem.telegram_user_id == telegram_user_id)
        .order_by(CartItem.id)
    )
    return list(result.all())


async def delete_cart_item(
    session: AsyncSession,
    cart_item: CartItem,
) -> None:
    await session.delete(cart_item)


async def clear_user_cart(
    session: AsyncSession,
    telegram_user_id: int,
) -> None:
    await session.execute(
        delete(CartItem).where(
            CartItem.telegram_user_id == telegram_user_id
        )
    )
