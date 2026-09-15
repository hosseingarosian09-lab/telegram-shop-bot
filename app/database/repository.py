from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Category, Product


async def get_active_categories(session: AsyncSession) -> list[Category]:
    result = await session.scalars(
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.id)
    )
    return list(result)


async def get_category(
    session: AsyncSession,
    category_id: int,
) -> Category | None:
    return await session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
        )
    )


async def get_products_by_category(
    session: AsyncSession,
    category_id: int,
) -> list[Product]:
    result = await session.scalars(
        select(Product)
        .join(Category, Category.id == Product.category_id)
        .where(
            Product.category_id == category_id,
            Product.is_active.is_(True),
            Category.is_active.is_(True),
        )
        .order_by(Product.id)
    )
    return list(result)


async def get_product(
    session: AsyncSession,
    product_id: int,
) -> Product | None:
    return await session.scalar(
        select(Product)
        .join(Category, Category.id == Product.category_id)
        .where(
            Product.id == product_id,
            Product.is_active.is_(True),
            Category.is_active.is_(True),
        )
    )
