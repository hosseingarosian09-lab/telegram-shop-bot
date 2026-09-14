from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.admin_catalog import AdminCategory, AdminProduct
from app.services.admin_orders import AdminOrder, ALLOWED_TRANSITIONS, status_label


def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Products", callback_data="admin:products")],
            [InlineKeyboardButton(text="🗂 Categories", callback_data="admin:categories")],
            [InlineKeyboardButton(text="📦 Orders", callback_data="admin:orders")],
        ]
    )


def categories_admin_keyboard(
    categories: list[AdminCategory],
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if c.is_active else '⛔'} {c.name}",
                callback_data=f"admin:category:{c.id}",
            )
        ]
        for c in categories
    ]
    rows.append(
        [InlineKeyboardButton(text="➕ Add Category", callback_data="admin:category:add")]
    )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Admin Menu", callback_data="admin:home")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_manage_keyboard(category: AdminCategory) -> InlineKeyboardMarkup:
    toggle_text = "⛔ Deactivate" if category.is_active else "✅ Activate"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Rename", callback_data=f"admin:category:rename:{category.id}")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin:category:toggle:{category.id}")],
            [InlineKeyboardButton(text="⬅️ Categories", callback_data="admin:categories")],
        ]
    )


def products_admin_keyboard(
    products: list[AdminProduct],
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if p.is_active else '⛔'} #{p.id} {p.name}",
                callback_data=f"admin:product:{p.id}",
            )
        ]
        for p in products
    ]
    rows.append(
        [InlineKeyboardButton(text="➕ Add Product", callback_data="admin:product:add")]
    )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Admin Menu", callback_data="admin:home")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_manage_keyboard(product: AdminProduct) -> InlineKeyboardMarkup:
    toggle_text = "⛔ Deactivate" if product.is_active else "✅ Activate"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Name", callback_data=f"admin:product:edit:{product.id}:name"),
                InlineKeyboardButton(text="✏️ Author", callback_data=f"admin:product:edit:{product.id}:author"),
            ],
            [
                InlineKeyboardButton(text="💰 Price", callback_data=f"admin:product:edit:{product.id}:price"),
                InlineKeyboardButton(text="📦 Stock", callback_data=f"admin:product:edit:{product.id}:stock"),
            ],
            [
                InlineKeyboardButton(text="📝 Description", callback_data=f"admin:product:edit:{product.id}:description"),
                InlineKeyboardButton(text="🗂 Category", callback_data=f"admin:product:edit:{product.id}:category"),
            ],
            [InlineKeyboardButton(text="🖼 Image", callback_data=f"admin:product:edit:{product.id}:image")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin:product:toggle:{product.id}")],
            [InlineKeyboardButton(text="⬅️ Products", callback_data="admin:products")],
        ]
    )


def category_choice_keyboard(
    categories: list[AdminCategory],
    prefix: str,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=category.name,
                callback_data=f"{prefix}:{category.id}",
            )
        ]
        for category in categories
        if category.is_active
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_orders_keyboard(
    orders: list[AdminOrder],
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"#{order.order_id} · {status_label(order.status)}",
                callback_data=f"admin:order:{order.order_id}",
            )
        ]
        for order in orders
    ]
    rows.append(
        [InlineKeyboardButton(text="⬅️ Admin Menu", callback_data="admin:home")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_detail_keyboard(order: AdminOrder) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    for next_status in sorted(ALLOWED_TRANSITIONS.get(order.status, set())):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"➡️ {status_label(next_status)}",
                    callback_data=f"admin:order:status:{order.order_id}:{next_status}",
                )
            ]
        )

    rows.append(
        [InlineKeyboardButton(text="⬅️ Orders", callback_data="admin:orders")]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
