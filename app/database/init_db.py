from app.database.base import Base
from app.database.seed import seed_catalog
from app.database.session import SessionFactory, engine


async def init_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with SessionFactory() as session:
        seeded = await seed_catalog(session)

    print("Database created and demo catalog seeded." if seeded else "Database ready.")
