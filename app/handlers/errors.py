import logging

from aiogram.exceptions import TelegramAPIError
from aiogram.types import ErrorEvent


logger = logging.getLogger(__name__)


async def global_error_handler(event: ErrorEvent) -> None:
    exception = event.exception
    logger.error(
        "Unhandled update error: %s",
        exception,
        exc_info=(type(exception), exception, exception.__traceback__),
    )

    try:
        callback = event.update.callback_query
        if callback is not None:
            await callback.answer(
                "یک خطای غیرمنتظره رخ داد. دوباره تلاش کنید یا /start را بزنید.",
                show_alert=True,
            )
            return

        message = event.update.message
        if message is not None:
            await message.answer(
                "⚠️ یک خطای غیرمنتظره رخ داد. دوباره تلاش کنید یا /start را بزنید."
            )
    except TelegramAPIError:
        logger.warning("Could not send the user-facing error message.")
