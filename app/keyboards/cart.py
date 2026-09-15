from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.cart import CartSnapshot


def cart_keyboard(snapshot: CartSnapshot) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for entry in snapshot.entries:
        row: list[InlineKeyboardButton] = []
        if entry.quantity > 1:
            row.append(
                InlineKeyboardButton(
                    text="➖",
                    callback_data=f"cart:dec:{entry.cart_item_id}",
                )
            )
        else:
            row.append(InlineKeyboardButton(text="−", callback_data="cart:noop"))

        row.append(
            InlineKeyboardButton(
                text=str(entry.quantity),
                callback_data="cart:noop",
            )
        )

        if entry.can_increase:
            row.append(
                InlineKeyboardButton(
                    text="➕",
                    callback_data=f"cart:inc:{entry.cart_item_id}",
                )
            )
        else:
            row.append(InlineKeyboardButton(text="+", callback_data="cart:noop"))

        row.append(
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"cart:remove:{entry.cart_item_id}",
            )
        )
        rows.append(row)

    if snapshot.can_checkout:
        rows.append(
            [InlineKeyboardButton(text="✅ ثبت سفارش", callback_data="cart:checkout")]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="⚠️ ابتدا مشکل سبد را رفع کنید", callback_data="cart:noop")]
        )

    rows.extend(
        [
            [InlineKeyboardButton(text="🗑 خالی کردن سبد", callback_data="cart:clear:confirm")],
            [InlineKeyboardButton(text="🛍 ادامه خرید", callback_data="catalog:categories")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="user:home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def empty_cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍 مشاهده کتاب‌ها", callback_data="catalog:categories")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="user:home")],
        ]
    )


def clear_cart_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ بله، خالی کن", callback_data="cart:clear:yes"),
                InlineKeyboardButton(text="❌ خیر", callback_data="cart:clear:no"),
            ]
        ]
    )
