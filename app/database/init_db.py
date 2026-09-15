import logging

from app.database.base import Base
from app.database.migrations import migrate_database
from app.database.seed import seed_catalog
from app.database.session import SessionFactory, engine


logger = logging.getLogger(__name__)


async def init_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await migrate_database()

    async with SessionFactory() as session:
        seeded = await seed_catalog(session)

    logger.info(
        "Database created and demo catalog seeded."
        if seeded
        else "Database ready."
    )
