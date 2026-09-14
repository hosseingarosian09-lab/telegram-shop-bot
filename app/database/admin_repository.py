from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Category, Order, Product


async def get_all_categories(session: AsyncSession) -> list[Category]:
    result = await session.scalars(
        select(Category).order_by(Category.id)
    )
    return list(result)


async def get_category_any(
    session: AsyncSession,
    category_id: int,
) -> Category | None:
    return await session.get(Category, category_id)


async def get_all_products(session: AsyncSession) -> list[Product]:
    result = await session.scalars(
        select(Product).order_by(Product.id)
    )
    return list(result)


async def get_product_any(
    session: AsyncSession,
    product_id: int,
) -> Product | None:
    return await session.get(Product, product_id)


async def get_latest_orders(
    session: AsyncSession,
    limit: int = 20,
) -> list[Order]:
    result = await session.scalars(
        select(Order)
        .order_by(Order.id.desc())
        .limit(limit)
    )
    return list(result)


async def get_order_any_with_items(
    session: AsyncSession,
    order_id: int,
) -> Order | None:
    return await session.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
