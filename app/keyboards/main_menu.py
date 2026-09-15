from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


HOME_BUTTON_TEXT = "🏠 شروع مجدد"

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🛍 محصولات"),
            KeyboardButton(text="🛒 سبد خرید"),
        ],
        [
            KeyboardButton(text="📦 سفارش‌های من"),
            KeyboardButton(text=HOME_BUTTON_TEXT),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="یک گزینه را انتخاب کنید",
)
