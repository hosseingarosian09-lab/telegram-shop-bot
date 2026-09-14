import asyncio

from aiogram import Bot, Dispatcher

from app.config import settings
from app.handlers.start import router as start_router


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.include_router(start_router)

    print("Bot is running with Long Polling.")
    print("Press Ctrl+C to stop.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
