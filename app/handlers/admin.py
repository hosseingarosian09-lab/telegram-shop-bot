from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.filters.admin import AdminFilter
from app.keyboards.admin import (
    admin_main_keyboard,
    admin_order_detail_keyboard,
    admin_orders_keyboard,
    categories_admin_keyboard,
    category_choice_keyboard,
    category_manage_keyboard,
    product_manage_keyboard,
    products_admin_keyboard,
)
from app.services.admin_catalog import (
    add_category,
    create_product,
    get_category,
    get_product,
    list_categories,
    list_products,
    remove_old_uploaded_image,
    rename_category,
    toggle_category,
    toggle_product,
    update_product_field,
)
from app.services.admin_orders import (
    change_order_status,
    get_admin_order,
    list_latest_orders,
    notify_customer_status,
    status_label,
)
from app.services.media import save_product_photo
from app.states.admin import (
    CategoryAdminStates,
    ProductAddStates,
    ProductEditStates,
)


entry_router = Router(name="admin_entry")
router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


def format_price(price: int) -> str:
    return f"{price:,} تومان"


async def show_admin_home(target) -> None:
    await target.answer(
        "🛠 Admin Panel",
        reply_markup=admin_main_keyboard(),
    )


@entry_router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext) -> None:
    await state.clear()

    user = message.from_user
    if user is None or user.id not in settings.admin_ids:
        await message.answer("⛔ شما به پنل مدیریت دسترسی ندارید.")
        return

    await show_admin_home(message)



# Registered before the FSM text handlers so /cancel is never consumed
# as a category/product field value.
@router.message(Command("cancel"))
async def admin_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()

    if current is None:
        await message.answer("Admin operation is not active.")
        return

    await state.clear()
    await message.answer("Admin operation cancelled.")


@router.callback_query(F.data == "admin:home")
async def admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    if callback.message is not None:
        await callback.message.edit_text(
            "🛠 Admin Panel",
            reply_markup=admin_main_keyboard(),
        )

    await callback.answer()


# ------------------------------------------------------------------
# Categories
# ------------------------------------------------------------------

@router.callback_query(F.data == "admin:categories")
async def admin_categories(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    categories = await list_categories()

    if callback.message is not None:
        await callback.message.edit_text(
            "🗂 Categories",
            reply_markup=categories_admin_keyboard(categories),
        )

    await callback.answer()


@router.callback_query(F.data == "admin:category:add")
async def admin_category_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryAdminStates.waiting_new_name)

    if callback.message is not None:
        await callback.message.answer(
            "نام دسته‌بندی جدید را ارسال کنید.\n"
            "برای لغو: /cancel"
        )

    await callback.answer()


@router.message(CategoryAdminStates.waiting_new_name)
async def admin_category_add_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()

    if len(name) < 2 or len(name) > 100:
        await message.answer("نام دسته‌بندی باید بین ۲ تا ۱۰۰ کاراکتر باشد.")
        return

    category = await add_category(name)
    await state.clear()

    await message.answer(
        f"✅ دسته‌بندی «{escape(category.name)}» ساخته شد.",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin:category:rename:"))
async def admin_category_rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        category_id = int(callback.data.rsplit(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("Invalid category.", show_alert=True)
        return

    category = await get_category(category_id)

    if category is None:
        await callback.answer("Category not found.", show_alert=True)
        return

    await state.update_data(category_id=category_id)
    await state.set_state(CategoryAdminStates.waiting_edit_name)

    if callback.message is not None:
        await callback.message.answer(
            f"نام جدید برای «{category.name}» را ارسال کنید.\n"
            "برای لغو: /cancel"
        )

    await callback.answer()


@router.message(CategoryAdminStates.waiting_edit_name)
async def admin_category_rename_finish(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()

    if len(name) < 2 or len(name) > 100:
        await message.answer("نام دسته‌بندی باید بین ۲ تا ۱۰۰ کاراکتر باشد.")
        return

    data = await state.get_data()
    success = await rename_category(data["category_id"], name)
    await state.clear()

    if success:
        await message.answer("✅ نام دسته‌بندی تغییر کرد.")
    else:
        await message.answer("❌ دسته‌بندی پیدا نشد.")


@router.callback_query(F.data.startswith("admin:category:toggle:"))
async def admin_category_toggle(callback: CallbackQuery) -> None:
    try:
        category_id = int(callback.data.rsplit(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("Invalid category.", show_alert=True)
        return

    category = await toggle_category(category_id)

    if category is None:
        await callback.answer("Category not found.", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            f"🗂 {escape(category.name)}\n"
            f"Status: {'Active ✅' if category.is_active else 'Inactive ⛔'}",
            parse_mode="HTML",
            reply_markup=category_manage_keyboard(category),
        )

    await callback.answer("Updated")


@router.callback_query(F.data.startswith("admin:category:"))
async def admin_category_detail(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    try:
        category_id = int(parts[2])
    except ValueError:
        await callback.answer("Invalid category.", show_alert=True)
        return

    category = await get_category(category_id)

    if category is None:
        await callback.answer("Category not found.", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            f"🗂 <b>{escape(category.name)}</b>\n"
            f"Status: {'Active ✅' if category.is_active else 'Inactive ⛔'}",
            parse_mode="HTML",
            reply_markup=category_manage_keyboard(category),
        )

    await callback.answer()


# ------------------------------------------------------------------
# Products
# ------------------------------------------------------------------

@router.callback_query(F.data == "admin:products")
async def admin_products(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    products = await list_products()

    if callback.message is not None:
        await callback.message.edit_text(
            "📚 Products",
            reply_markup=products_admin_keyboard(products),
        )

    await callback.answer()


@router.callback_query(F.data == "admin:product:add")
async def admin_product_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    categories = await list_categories()
    active_categories = [c for c in categories if c.is_active]

    if not active_categories:
        await callback.answer(
            "ابتدا حداقل یک دسته‌بندی فعال بسازید.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(ProductAddStates.waiting_category)

    if callback.message is not None:
        await callback.message.answer(
            "دسته‌بندی محصول را انتخاب کنید:",
            reply_markup=category_choice_keyboard(
                active_categories,
                "admin:add_product:category",
            ),
        )

    await callback.answer()


@router.callback_query(
    ProductAddStates.waiting_category,
    F.data.startswith("admin:add_product:category:"),
)
async def admin_product_add_category(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        category_id = int(callback.data.rsplit(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("Invalid category.", show_alert=True)
        return

    category = await get_category(category_id)

    if category is None or not category.is_active:
        await callback.answer("Category is not available.", show_alert=True)
        return

    await state.update_data(category_id=category_id)
    await state.set_state(ProductAddStates.waiting_name)

    if callback.message is not None:
        await callback.message.answer("نام کتاب را ارسال کنید:")

    await callback.answer()


@router.message(ProductAddStates.waiting_name)
async def admin_product_add_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if len(value) < 2 or len(value) > 200:
        await message.answer("نام باید بین ۲ تا ۲۰۰ کاراکتر باشد.")
        return

    await state.update_data(name=value)
    await state.set_state(ProductAddStates.waiting_author)
    await message.answer("نام نویسنده را ارسال کنید:")


@router.message(ProductAddStates.waiting_author)
async def admin_product_add_author(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if len(value) < 2 or len(value) > 160:
        await message.answer("نام نویسنده باید بین ۲ تا ۱۶۰ کاراکتر باشد.")
        return

    await state.update_data(author=value)
    await state.set_state(ProductAddStates.waiting_price)
    await message.answer("قیمت را به تومان و فقط به صورت عدد وارد کنید:")


@router.message(ProductAddStates.waiting_price)
async def admin_product_add_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(",", "").strip()

    if not raw.isdigit() or int(raw) <= 0:
        await message.answer("قیمت باید یک عدد صحیح مثبت باشد.")
        return

    await state.update_data(price=int(raw))
    await state.set_state(ProductAddStates.waiting_stock)
    await message.answer("موجودی را به صورت عدد صحیح صفر یا بیشتر وارد کنید:")


@router.message(ProductAddStates.waiting_stock)
async def admin_product_add_stock(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()

    if not raw.isdigit():
        await message.answer("موجودی باید عدد صحیح صفر یا بیشتر باشد.")
        return

    await state.update_data(stock=int(raw))
    await state.set_state(ProductAddStates.waiting_description)
    await message.answer("توضیحات کتاب را ارسال کنید:")


@router.message(ProductAddStates.waiting_description)
async def admin_product_add_description(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()

    if len(value) < 5 or len(value) > 1500:
        await message.answer("توضیحات باید بین ۵ تا ۱۵۰۰ کاراکتر باشد.")
        return

    await state.update_data(description=value)
    await state.set_state(ProductAddStates.waiting_image)

    await message.answer(
        "یک عکس برای کتاب ارسال کنید.\n"
        "یا /skip را بفرستید تا از تصویر پیش‌فرض استفاده شود."
    )


@router.message(ProductAddStates.waiting_image, F.photo)
async def admin_product_add_image(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    image_path = await save_product_photo(bot, message.photo[-1])
    data = await state.get_data()

    product = await create_product(
        category_id=data["category_id"],
        name=data["name"],
        author=data["author"],
        price=data["price"],
        stock=data["stock"],
        description=data["description"],
        image_path=image_path,
    )

    await state.clear()

    if product is None:
        remove_old_uploaded_image(image_path)
        await message.answer("❌ ساخت محصول ناموفق بود.")
        return

    await message.answer(
        f"✅ کتاب «{product.name}» با ID #{product.id} ساخته شد."
    )


@router.message(ProductAddStates.waiting_image, Command("skip"))
async def admin_product_add_skip_image(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    product = await create_product(
        category_id=data["category_id"],
        name=data["name"],
        author=data["author"],
        price=data["price"],
        stock=data["stock"],
        description=data["description"],
        image_path=None,
    )

    await state.clear()

    if product is None:
        await message.answer("❌ ساخت محصول ناموفق بود.")
        return

    await message.answer(
        f"✅ کتاب «{product.name}» با ID #{product.id} ساخته شد."
    )



@router.message(ProductAddStates.waiting_image)
async def admin_product_add_image_fallback(message: Message) -> None:
    await message.answer(
        "لطفاً یک عکس ارسال کنید، یا /skip را برای تصویر پیش‌فرض بفرستید، "
        "یا /cancel را برای لغو استفاده کنید."
    )


@router.callback_query(F.data.startswith("admin:product:toggle:"))
async def admin_product_toggle(callback: CallbackQuery) -> None:
    try:
        product_id = int(callback.data.rsplit(":", 1)[1])
    except (TypeError, ValueError):
        await callback.answer("Invalid product.", show_alert=True)
        return

    product = await toggle_product(product_id)

    if product is None:
        await callback.answer("Product not found.", show_alert=True)
        return

    if callback.message is not None:
        await show_product_detail(callback.message, product)

    await callback.answer("Updated")


@router.callback_query(F.data.startswith("admin:product:edit:"))
async def admin_product_edit_start(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":") if callback.data else []

    if len(parts) != 5:
        await callback.answer("Invalid edit action.", show_alert=True)
        return

    try:
        product_id = int(parts[3])
    except ValueError:
        await callback.answer("Invalid product.", show_alert=True)
        return

    field = parts[4]
    product = await get_product(product_id)

    if product is None:
        await callback.answer("Product not found.", show_alert=True)
        return

    if field == "category":
        categories = [c for c in await list_categories() if c.is_active]

        if callback.message is not None:
            await callback.message.answer(
                "دسته‌بندی جدید را انتخاب کنید:",
                reply_markup=category_choice_keyboard(
                    categories,
                    f"admin:edit_product:category:{product_id}",
                ),
            )

        await callback.answer()
        return

    await state.clear()
    await state.update_data(product_id=product_id, field=field)

    if field == "image":
        await state.set_state(ProductEditStates.waiting_image)

        if callback.message is not None:
            await callback.message.answer(
                "عکس جدید را ارسال کنید.\nبرای لغو: /cancel"
            )
    else:
        await state.set_state(ProductEditStates.waiting_value)

        prompts = {
            "name": "نام جدید را ارسال کنید:",
            "author": "نام نویسنده جدید را ارسال کنید:",
            "price": "قیمت جدید را فقط به صورت عدد وارد کنید:",
            "stock": "موجودی جدید را فقط به صورت عدد وارد کنید:",
            "description": "توضیحات جدید را ارسال کنید:",
        }

        if callback.message is not None:
            await callback.message.answer(prompts[field])

    await callback.answer()


@router.callback_query(F.data.startswith("admin:edit_product:category:"))
async def admin_product_edit_category(callback: CallbackQuery) -> None:
    parts = callback.data.split(":") if callback.data else []

    if len(parts) != 5:
        await callback.answer("Invalid action.", show_alert=True)
        return

    try:
        product_id = int(parts[3])
        category_id = int(parts[4])
    except ValueError:
        await callback.answer("Invalid IDs.", show_alert=True)
        return

    success = await update_product_field(
        product_id,
        "category_id",
        category_id,
    )

    await callback.answer(
        "Category updated" if success else "Update failed",
        show_alert=not success,
    )


@router.message(ProductEditStates.waiting_value)
async def admin_product_edit_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = data["product_id"]
    field = data["field"]
    raw = (message.text or "").strip()

    value = raw

    if field == "price":
        raw = raw.replace(",", "")
        if not raw.isdigit() or int(raw) <= 0:
            await message.answer("قیمت باید یک عدد صحیح مثبت باشد.")
            return
        value = int(raw)

    elif field == "stock":
        if not raw.isdigit():
            await message.answer("موجودی باید عدد صحیح صفر یا بیشتر باشد.")
            return
        value = int(raw)

    elif field in {"name", "author"}:
        if len(raw) < 2:
            await message.answer("مقدار واردشده خیلی کوتاه است.")
            return

    elif field == "description":
        if len(raw) < 5:
            await message.answer("توضیحات خیلی کوتاه است.")
            return

    success = await update_product_field(product_id, field, value)
    await state.clear()

    await message.answer(
        "✅ محصول ویرایش شد." if success else "❌ ویرایش ناموفق بود."
    )


@router.message(ProductEditStates.waiting_image, F.photo)
async def admin_product_edit_image(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    product_id = data["product_id"]
    old_product = await get_product(product_id)

    if old_product is None:
        await state.clear()
        await message.answer("❌ محصول پیدا نشد.")
        return

    new_path = await save_product_photo(bot, message.photo[-1])
    success = await update_product_field(
        product_id,
        "image_path",
        new_path,
    )
    await state.clear()

    if success:
        remove_old_uploaded_image(old_product.image_path)
        await message.answer("✅ تصویر محصول تغییر کرد.")
    else:
        remove_old_uploaded_image(new_path)
        await message.answer("❌ تغییر تصویر ناموفق بود.")



@router.message(ProductEditStates.waiting_image)
async def admin_product_edit_image_fallback(message: Message) -> None:
    await message.answer(
        "لطفاً عکس جدید را ارسال کنید یا /cancel را برای لغو استفاده کنید."
    )


async def show_product_detail(target_message, product) -> None:
    text = (
        f"📚 <b>#{product.id} {escape(product.name)}</b>\n"
        f"✍️ {escape(product.author)}\n"
        f"🗂 {escape(product.category_name)}\n"
        f"💰 {format_price(product.price)}\n"
        f"📦 Stock: {product.stock}\n"
        f"Status: {'Active ✅' if product.is_active else 'Inactive ⛔'}\n\n"
        f"{escape(product.description)}"
    )

    await target_message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=product_manage_keyboard(product),
    )


@router.callback_query(F.data.startswith("admin:product:"))
async def admin_product_detail(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    try:
        product_id = int(parts[2])
    except ValueError:
        await callback.answer("Invalid product.", show_alert=True)
        return

    product = await get_product(product_id)

    if product is None:
        await callback.answer("Product not found.", show_alert=True)
        return

    if callback.message is not None:
        await show_product_detail(callback.message, product)

    await callback.answer()


# ------------------------------------------------------------------
# Orders
# ------------------------------------------------------------------

@router.callback_query(F.data == "admin:orders")
async def admin_orders(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    orders = await list_latest_orders()

    if callback.message is not None:
        await callback.message.edit_text(
            "📦 Latest Orders",
            reply_markup=admin_orders_keyboard(orders),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:status:"))
async def admin_order_status(
    callback: CallbackQuery,
    bot: Bot,
) -> None:
    parts = callback.data.split(":") if callback.data else []

    if len(parts) != 5:
        await callback.answer("Invalid action.", show_alert=True)
        return

    try:
        order_id = int(parts[3])
    except ValueError:
        await callback.answer("Invalid order.", show_alert=True)
        return

    new_status = parts[4]

    order, message = await change_order_status(order_id, new_status)

    if order is None:
        await callback.answer(message, show_alert=True)
        return

    notified = await notify_customer_status(
        bot,
        telegram_user_id=order.telegram_user_id,
        order_id=order.order_id,
        status=order.status,
    )

    if callback.message is not None:
        await show_admin_order(callback.message, order)

    await callback.answer(
        "Status updated" + ("" if notified else " (customer notification failed)")
    )


@router.callback_query(F.data.startswith("admin:order:"))
async def admin_order_detail(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    try:
        order_id = int(parts[2])
    except ValueError:
        await callback.answer("Invalid order.", show_alert=True)
        return

    order = await get_admin_order(order_id)

    if order is None:
        await callback.answer("Order not found.", show_alert=True)
        return

    if callback.message is not None:
        await show_admin_order(callback.message, order)

    await callback.answer()


async def show_admin_order(target_message, order) -> None:
    lines = [
        f"📦 <b>Order #{order.order_id}</b>",
        f"Status: <b>{escape(status_label(order.status))}</b>",
        f"Telegram User ID: <code>{order.telegram_user_id}</code>",
        f"Date: {escape(order.created_at_text)}",
        "",
        f"👤 {escape(order.customer_name)}",
        f"📞 {escape(order.phone)}",
        f"📍 {escape(order.address)}",
        "",
        "📚 <b>Items:</b>",
    ]

    for item in order.items:
        lines.append(
            f"• {escape(item.product_name)} × {item.quantity} "
            f"= {format_price(item.subtotal)}"
        )

    lines.extend(
        [
            "",
            f"💰 <b>Total: {format_price(order.total_amount)}</b>",
        ]
    )

    await target_message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=admin_order_detail_keyboard(order),
    )


