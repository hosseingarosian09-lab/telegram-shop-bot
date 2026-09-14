from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🛍 محصولات"),
            KeyboardButton(text="🛒 سبد خرید"),
        ],
        [
            KeyboardButton(text="📦 سفارش‌های من"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="یک گزینه را انتخاب کنید",
)
