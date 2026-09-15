from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import Category, Product


def categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=category.name,
                callback_data=f"category:{category.id}",
            )
        ]
        for category in categories
    ]
    rows.append(
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="user:home")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_keyboard(products: list[Product]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"📚 {product.name}",
                callback_data=f"product:{product.id}",
            )
        ]
        for product in products
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="⬅️ دسته‌بندی‌ها", callback_data="catalog:categories")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="user:home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_detail_keyboard(
    product_id: int,
    category_id: int,
    stock: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if stock > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🛒 افزودن به سبد",
                    callback_data=f"cart:add:{product_id}",
                )
            ]
        )

    rows.extend(
        [
            [InlineKeyboardButton(text="🛒 مشاهده سبد", callback_data="cart:show")],
            [InlineKeyboardButton(text="⬅️ برگشت به کتاب‌ها", callback_data=f"category:{category_id}")],
            [InlineKeyboardButton(text="📚 دسته‌بندی‌ها", callback_data="catalog:categories")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="user:home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
