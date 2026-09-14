from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def checkout_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ لغو تسویه حساب", callback_data="checkout:cancel")]
        ]
    )


def checkout_review_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید و ثبت سفارش", callback_data="checkout:confirm")],
            [InlineKeyboardButton(text="❌ لغو", callback_data="checkout:cancel")],
        ]
    )


def checkout_failed_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 برگشت به سبد خرید", callback_data="cart:show")]
        ]
    )
