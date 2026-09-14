import asyncio

from aiogram import Bot, Dispatcher

from app.config import settings
from app.database.init_db import init_database
from app.handlers.admin import entry_router as admin_entry_router
from app.handlers.admin import router as admin_router
from app.handlers.cart import router as cart_router
from app.handlers.catalog import router as catalog_router
from app.handlers.checkout import router as checkout_router
from app.handlers.orders import router as orders_router
from app.handlers.start import router as start_router


async def main() -> None:
    await init_database()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(admin_entry_router)
    dp.include_router(admin_router)
    dp.include_router(checkout_router)
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(orders_router)

    print("Bot is running with Long Polling.")
    print("Press Ctrl+C to stop.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
