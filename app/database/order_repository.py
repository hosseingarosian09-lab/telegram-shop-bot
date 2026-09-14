from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Order


async def get_user_orders(
    session: AsyncSession,
    telegram_user_id: int,
    limit: int = 10,
) -> list[Order]:
    result = await session.scalars(
        select(Order)
        .where(Order.telegram_user_id == telegram_user_id)
        .order_by(Order.id.desc())
        .limit(limit)
    )
    return list(result)


async def get_user_order_with_items(
    session: AsyncSession,
    telegram_user_id: int,
    order_id: int,
) -> Order | None:
    return await session.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(
            Order.id == order_id,
            Order.telegram_user_id == telegram_user_id,
        )
    )
