from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.cart import CartSnapshot


def cart_keyboard(snapshot: CartSnapshot) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for entry in snapshot.entries:
        rows.append(
            [
                InlineKeyboardButton(
                    text="➖",
                    callback_data=f"cart:dec:{entry.cart_item_id}",
                ),
                InlineKeyboardButton(
                    text=str(entry.quantity),
                    callback_data="cart:noop",
                ),
                InlineKeyboardButton(
                    text="➕",
                    callback_data=f"cart:inc:{entry.cart_item_id}",
                ),
                InlineKeyboardButton(
                    text="🗑",
                    callback_data=f"cart:remove:{entry.cart_item_id}",
                ),
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="🗑 خالی کردن سبد",
                callback_data="cart:clear:confirm",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text="🛍 ادامه خرید",
                callback_data="catalog:categories",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def empty_cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 مشاهده کتاب‌ها",
                    callback_data="catalog:categories",
                )
            ]
        ]
    )


def clear_cart_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، خالی کن",
                    callback_data="cart:clear:yes",
                ),
                InlineKeyboardButton(
                    text="❌ خیر",
                    callback_data="cart:clear:no",
                ),
            ]
        ]
    )
