from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import Category, Product


def categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c.name, callback_data=f"category:{c.id}")] for c in categories
    ])


def products_keyboard(products: list[Product]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"📚 {p.name}", callback_data=f"product:{p.id}")] for p in products]
    rows.append([InlineKeyboardButton(text="⬅️ دسته‌بندی‌ها", callback_data="catalog:categories")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_detail_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ برگشت به کتاب‌ها", callback_data=f"category:{category_id}")],
        [InlineKeyboardButton(text="🏠 دسته‌بندی‌ها", callback_data="catalog:categories")],
    ])
