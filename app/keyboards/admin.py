from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.admin_catalog import AdminCategory, AdminProduct
from app.services.admin_orders import AdminOrder, allowed_next_statuses, status_label


def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 مدیریت محصولات", callback_data="admin:products")],
            [InlineKeyboardButton(text="🗂 مدیریت دسته‌بندی‌ها", callback_data="admin:categories")],
            [InlineKeyboardButton(text="📦 مدیریت سفارش‌ها", callback_data="admin:orders")],
            [InlineKeyboardButton(text="🏠 منوی فروشگاه", callback_data="user:home")],
        ]
    )


def admin_navigation_keyboard(
    back_callback: str,
    back_text: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⬅️ {back_text}", callback_data=back_callback)],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )


def categories_admin_keyboard(categories: list[AdminCategory]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if c.is_active else '⛔'} {c.name}",
                callback_data=f"admin:category:{c.id}",
            )
        ]
        for c in categories
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="➕ افزودن دسته‌بندی", callback_data="admin:category:add")],
            [InlineKeyboardButton(text="⬅️ پنل مدیریت", callback_data="admin:home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_manage_keyboard(category: AdminCategory) -> InlineKeyboardMarkup:
    toggle_text = "⛔ غیرفعال کردن" if category.is_active else "✅ فعال کردن"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ تغییر نام", callback_data=f"admin:category:rename:{category.id}")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin:category:toggle:{category.id}")],
            [InlineKeyboardButton(text="🗑 حذف دسته‌بندی", callback_data=f"admin:category:delete:{category.id}")],
            [InlineKeyboardButton(text="⬅️ دسته‌بندی‌ها", callback_data="admin:categories")],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )


def category_delete_confirmation_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 بله، حذف شود", callback_data=f"admin:category:delete_yes:{category_id}")],
            [InlineKeyboardButton(text="❌ خیر", callback_data=f"admin:category:{category_id}")],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )


def products_admin_keyboard(products: list[AdminProduct]) -> InlineKeyboardMarkup:
    rows = []
    for product in products:
        product_icon = "✅" if product.is_active else "⛔"
        category_icon = "" if product.category_active else " ⚠️"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{product_icon}{category_icon} #{product.id} {product.name}",
                    callback_data=f"admin:product:{product.id}",
                )
            ]
        )

    rows.extend(
        [
            [InlineKeyboardButton(text="➕ افزودن محصول", callback_data="admin:product:add")],
            [InlineKeyboardButton(text="⬅️ پنل مدیریت", callback_data="admin:home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_manage_keyboard(product: AdminProduct) -> InlineKeyboardMarkup:
    toggle_text = "⛔ غیرفعال کردن" if product.is_active else "✅ فعال کردن"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ نام", callback_data=f"admin:product:edit:{product.id}:name"),
                InlineKeyboardButton(text="✏️ نویسنده", callback_data=f"admin:product:edit:{product.id}:author"),
            ],
            [
                InlineKeyboardButton(text="💰 قیمت", callback_data=f"admin:product:edit:{product.id}:price"),
                InlineKeyboardButton(text="📦 موجودی", callback_data=f"admin:product:edit:{product.id}:stock"),
            ],
            [
                InlineKeyboardButton(text="📝 توضیحات", callback_data=f"admin:product:edit:{product.id}:description"),
                InlineKeyboardButton(text="🗂 دسته‌بندی", callback_data=f"admin:product:edit:{product.id}:category"),
            ],
            [InlineKeyboardButton(text="🖼 تصویر", callback_data=f"admin:product:edit:{product.id}:image")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin:product:toggle:{product.id}")],
            [InlineKeyboardButton(text="🗑 حذف محصول", callback_data=f"admin:product:delete:{product.id}")],
            [InlineKeyboardButton(text="⬅️ محصولات", callback_data="admin:products")],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )


def product_delete_confirmation_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 بله، حذف شود", callback_data=f"admin:product:delete_yes:{product_id}")],
            [InlineKeyboardButton(text="❌ خیر", callback_data=f"admin:product:{product_id}")],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )


def category_choice_keyboard(
    categories: list[AdminCategory],
    prefix: str,
    back_callback: str,
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
    rows.extend(
        [
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data=back_callback)],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_orders_keyboard(
    orders: list[AdminOrder],
    archived: bool = False,
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

    if archived:
        rows.append(
            [InlineKeyboardButton(text="📦 سفارش‌های فعال", callback_data="admin:orders")]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="🗄 سفارش‌های آرشیوشده", callback_data="admin:orders:archived")]
        )

    rows.append(
        [InlineKeyboardButton(text="⬅️ پنل مدیریت", callback_data="admin:home")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_detail_keyboard(order: AdminOrder) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if not order.is_archived:
        for next_status in allowed_next_statuses(order.status):
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"➡️ {status_label(next_status)}",
                        callback_data=f"admin:order:status:{order.order_id}:{next_status}",
                    )
                ]
            )
        rows.append(
            [InlineKeyboardButton(text="🗑 حذف از لیست (آرشیو)", callback_data=f"admin:order:archive:{order.order_id}")]
        )
        back_callback = "admin:orders"
        back_text = "سفارش‌ها"
    else:
        rows.append(
            [InlineKeyboardButton(text="♻️ بازگردانی از آرشیو", callback_data=f"admin:order:restore:{order.order_id}")]
        )
        back_callback = "admin:orders:archived"
        back_text = "آرشیو"

    rows.extend(
        [
            [InlineKeyboardButton(text=f"⬅️ {back_text}", callback_data=back_callback)],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_archive_confirmation_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 بله، آرشیو شود", callback_data=f"admin:order:archive_yes:{order_id}")],
            [InlineKeyboardButton(text="❌ خیر", callback_data=f"admin:order:{order_id}")],
            [InlineKeyboardButton(text="🏠 پنل مدیریت", callback_data="admin:home")],
        ]
    )
