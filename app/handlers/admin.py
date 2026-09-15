from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.filters.admin import AdminFilter
from app.keyboards.admin import (
    admin_main_keyboard,
    admin_navigation_keyboard,
    admin_order_detail_keyboard,
    admin_orders_keyboard,
    categories_admin_keyboard,
    category_choice_keyboard,
    category_delete_confirmation_keyboard,
    category_manage_keyboard,
    order_archive_confirmation_keyboard,
    product_delete_confirmation_keyboard,
    product_manage_keyboard,
    products_admin_keyboard,
)
from app.services.admin_catalog import (
    add_category,
    create_product,
    delete_category,
    delete_product,
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
    set_order_archived,
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


def form_navigation(back_callback: str, back_text: str):
    return admin_navigation_keyboard(back_callback, back_text)


@entry_router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext) -> None:
    await state.clear()

    user = message.from_user
    if user is None or user.id not in settings.admin_ids:
        await message.answer("⛔ شما به پنل مدیریت دسترسی ندارید.")
        return

    await message.answer(
        "🛠 <b>پنل مدیریت</b>",
        parse_mode="HTML",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin:home")
async def admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(
            "🛠 <b>پنل مدیریت</b>",
            parse_mode="HTML",
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
            "🗂 <b>مدیریت دسته‌بندی‌ها</b>",
            parse_mode="HTML",
            reply_markup=categories_admin_keyboard(categories),
        )
    await callback.answer()


@router.callback_query(F.data == "admin:category:add")
async def admin_category_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CategoryAdminStates.waiting_new_name)

    if callback.message is not None:
        await callback.message.answer(
            "نام دسته‌بندی جدید را ارسال کنید:",
            reply_markup=form_navigation("admin:categories", "دسته‌بندی‌ها"),
        )
    await callback.answer()


@router.message(CategoryAdminStates.waiting_new_name)
async def admin_category_add_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 100:
        await message.answer(
            "نام دسته‌بندی باید بین ۲ تا ۱۰۰ کاراکتر باشد.",
            reply_markup=form_navigation("admin:categories", "دسته‌بندی‌ها"),
        )
        return

    category, result_message = await add_category(name)
    if category is None:
        await message.answer(
            f"❌ {result_message}",
            reply_markup=form_navigation("admin:categories", "دسته‌بندی‌ها"),
        )
        return

    await state.clear()
    await message.answer(
        f"✅ دسته‌بندی «{escape(category.name)}» ساخته شد.",
        parse_mode="HTML",
        reply_markup=category_manage_keyboard(category),
    )


@router.callback_query(F.data.startswith("admin:category:rename:"))
async def admin_category_rename_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    try:
        category_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("دسته‌بندی نامعتبر است.", show_alert=True)
        return

    category = await get_category(category_id)
    if category is None:
        await callback.answer("دسته‌بندی پیدا نشد.", show_alert=True)
        return

    await state.clear()
    await state.update_data(category_id=category_id)
    await state.set_state(CategoryAdminStates.waiting_edit_name)

    if callback.message is not None:
        await callback.message.answer(
            f"نام جدید برای «{category.name}» را ارسال کنید:",
            reply_markup=form_navigation(
                f"admin:category:{category_id}",
                "دسته‌بندی",
            ),
        )
    await callback.answer()


@router.message(CategoryAdminStates.waiting_edit_name)
async def admin_category_rename_finish(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    data = await state.get_data()
    category_id = int(data["category_id"])

    if len(name) < 2 or len(name) > 100:
        await message.answer(
            "نام دسته‌بندی باید بین ۲ تا ۱۰۰ کاراکتر باشد.",
            reply_markup=form_navigation(
                f"admin:category:{category_id}",
                "دسته‌بندی",
            ),
        )
        return

    category, result_message = await rename_category(category_id, name)
    if category is None:
        await message.answer(
            f"❌ {result_message}",
            reply_markup=form_navigation("admin:categories", "دسته‌بندی‌ها"),
        )
        return

    await state.clear()
    await message.answer(
        "✅ نام دسته‌بندی تغییر کرد.",
        reply_markup=category_manage_keyboard(category),
    )


@router.callback_query(F.data.startswith("admin:category:toggle:"))
async def admin_category_toggle(callback: CallbackQuery) -> None:
    try:
        category_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("دسته‌بندی نامعتبر است.", show_alert=True)
        return

    category = await toggle_category(category_id)
    if category is None:
        await callback.answer("دسته‌بندی پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await show_category_detail(callback.message, category)
    await callback.answer("وضعیت تغییر کرد.")


@router.callback_query(F.data.startswith("admin:category:delete:"))
async def admin_category_delete_confirm(callback: CallbackQuery) -> None:
    try:
        category_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("دسته‌بندی نامعتبر است.", show_alert=True)
        return

    category = await get_category(category_id)
    if category is None:
        await callback.answer("دسته‌بندی پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            f"🗑 حذف دسته‌بندی «{escape(category.name)}»؟\n\n"
            "حذف فقط زمانی انجام می‌شود که هیچ محصولی داخل این دسته‌بندی نباشد.",
            parse_mode="HTML",
            reply_markup=category_delete_confirmation_keyboard(category_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:category:delete_yes:"))
async def admin_category_delete_yes(callback: CallbackQuery) -> None:
    try:
        category_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("دسته‌بندی نامعتبر است.", show_alert=True)
        return

    success, message = await delete_category(category_id)
    if callback.message is not None:
        await callback.message.edit_text(
            ("✅ " if success else "❌ ") + escape(message),
            parse_mode="HTML",
            reply_markup=form_navigation("admin:categories", "دسته‌بندی‌ها"),
        )
    await callback.answer()


async def show_category_detail(target_message, category) -> None:
    await target_message.edit_text(
        f"🗂 <b>{escape(category.name)}</b>\n"
        f"وضعیت: {'فعال ✅' if category.is_active else 'غیرفعال ⛔'}",
        parse_mode="HTML",
        reply_markup=category_manage_keyboard(category),
    )


@router.callback_query(F.data.startswith("admin:category:"))
async def admin_category_detail(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        return

    try:
        category_id = int(parts[2])
    except ValueError:
        await callback.answer("دسته‌بندی نامعتبر است.", show_alert=True)
        return

    await state.clear()
    category = await get_category(category_id)
    if category is None:
        await callback.answer("دسته‌بندی پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await show_category_detail(callback.message, category)
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
            "📚 <b>مدیریت محصولات</b>\n\n"
            "⚠️ کنار محصول یعنی دسته‌بندی آن غیرفعال است.",
            parse_mode="HTML",
            reply_markup=products_admin_keyboard(products),
        )
    await callback.answer()


@router.callback_query(F.data == "admin:product:add")
async def admin_product_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    categories = [c for c in await list_categories() if c.is_active]
    if not categories:
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
                categories,
                "admin:add_product:category",
                "admin:products",
            ),
        )
    await callback.answer()


@router.callback_query(
    ProductAddStates.waiting_category,
    F.data.startswith("admin:add_product:category:"),
)
async def admin_product_add_category(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    try:
        category_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("دسته‌بندی نامعتبر است.", show_alert=True)
        return

    category = await get_category(category_id)
    if category is None or not category.is_active:
        await callback.answer("این دسته‌بندی فعال نیست.", show_alert=True)
        return

    await state.update_data(category_id=category_id)
    await state.set_state(ProductAddStates.waiting_name)
    if callback.message is not None:
        await callback.message.edit_text(
            f"✅ دسته‌بندی انتخاب شد: {escape(category.name)}",
            parse_mode="HTML",
        )
        await callback.message.answer(
            "نام کتاب را ارسال کنید:",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
    await callback.answer()


@router.message(ProductAddStates.waiting_name)
async def admin_product_add_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 2 or len(value) > 200:
        await message.answer(
            "نام باید بین ۲ تا ۲۰۰ کاراکتر باشد.",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
        return

    await state.update_data(name=value)
    await state.set_state(ProductAddStates.waiting_author)
    await message.answer(
        "نام نویسنده را ارسال کنید:",
        reply_markup=form_navigation("admin:products", "محصولات"),
    )


@router.message(ProductAddStates.waiting_author)
async def admin_product_add_author(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 2 or len(value) > 160:
        await message.answer(
            "نام نویسنده باید بین ۲ تا ۱۶۰ کاراکتر باشد.",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
        return

    await state.update_data(author=value)
    await state.set_state(ProductAddStates.waiting_price)
    await message.answer(
        "قیمت را به تومان و فقط به صورت عدد وارد کنید:\nقیمت باید بیشتر از صفر باشد.",
        reply_markup=form_navigation("admin:products", "محصولات"),
    )


@router.message(ProductAddStates.waiting_price)
async def admin_product_add_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(",", "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer(
            "قیمت باید یک عدد صحیح بزرگ‌تر از صفر باشد.",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
        return

    await state.update_data(price=int(raw))
    await state.set_state(ProductAddStates.waiting_stock)
    await message.answer(
        "موجودی را به صورت عدد صحیح صفر یا بیشتر وارد کنید:",
        reply_markup=form_navigation("admin:products", "محصولات"),
    )


@router.message(ProductAddStates.waiting_stock)
async def admin_product_add_stock(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(
            "موجودی باید عدد صحیح صفر یا بیشتر باشد.",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
        return

    await state.update_data(stock=int(raw))
    await state.set_state(ProductAddStates.waiting_description)
    await message.answer(
        "توضیحات کتاب را ارسال کنید:",
        reply_markup=form_navigation("admin:products", "محصولات"),
    )


@router.message(ProductAddStates.waiting_description)
async def admin_product_add_description(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 5 or len(value) > 1500:
        await message.answer(
            "توضیحات باید بین ۵ تا ۱۵۰۰ کاراکتر باشد.",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
        return

    await state.update_data(description=value)
    await state.set_state(ProductAddStates.waiting_image)
    await message.answer(
        "یک عکس برای کتاب ارسال کنید.\n"
        "یا /skip را بفرستید تا تصویر پیش‌فرض استفاده شود.",
        reply_markup=form_navigation("admin:products", "محصولات"),
    )


async def _finish_product_create(
    message: Message,
    state: FSMContext,
    image_path: str | None,
) -> None:
    data = await state.get_data()
    product, result_message = await create_product(
        category_id=data["category_id"],
        name=data["name"],
        author=data["author"],
        price=data["price"],
        stock=data["stock"],
        description=data["description"],
        image_path=image_path,
    )

    if product is None:
        if image_path:
            remove_old_uploaded_image(image_path)
        await message.answer(
            f"❌ {result_message}",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
        return

    await state.clear()
    await message.answer(
        f"✅ کتاب «{escape(product.name)}» با ID #{product.id} ساخته شد.",
        parse_mode="HTML",
        reply_markup=product_manage_keyboard(product),
    )


@router.message(ProductAddStates.waiting_image, F.photo)
async def admin_product_add_image(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    image_path = await save_product_photo(bot, message.photo[-1])
    await _finish_product_create(message, state, image_path)


@router.message(ProductAddStates.waiting_image, Command("skip"))
async def admin_product_add_skip_image(message: Message, state: FSMContext) -> None:
    await _finish_product_create(message, state, None)


@router.message(ProductAddStates.waiting_image)
async def admin_product_add_image_fallback(message: Message) -> None:
    await message.answer(
        "لطفاً یک عکس ارسال کنید یا /skip را برای تصویر پیش‌فرض بفرستید.",
        reply_markup=form_navigation("admin:products", "محصولات"),
    )


@router.callback_query(F.data.startswith("admin:product:toggle:"))
async def admin_product_toggle(callback: CallbackQuery) -> None:
    try:
        product_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("محصول نامعتبر است.", show_alert=True)
        return

    product = await toggle_product(product_id)
    if product is None:
        await callback.answer("محصول پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await show_product_detail(callback.message, product)
    await callback.answer("وضعیت تغییر کرد.")


@router.callback_query(F.data.startswith("admin:product:delete:"))
async def admin_product_delete_confirm(callback: CallbackQuery) -> None:
    try:
        product_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("محصول نامعتبر است.", show_alert=True)
        return

    product = await get_product(product_id)
    if product is None:
        await callback.answer("محصول پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            f"🗑 حذف «{escape(product.name)}»؟\n\n"
            "اگر این محصول در سابقه سفارش‌ها استفاده شده باشد، برای حفظ تاریخچه "
            "به‌جای حذف کامل، غیرفعال می‌شود.",
            parse_mode="HTML",
            reply_markup=product_delete_confirmation_keyboard(product_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:product:delete_yes:"))
async def admin_product_delete_yes(callback: CallbackQuery) -> None:
    try:
        product_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("محصول نامعتبر است.", show_alert=True)
        return

    result, message = await delete_product(product_id)
    success = result in {"deleted", "deactivated"}
    if callback.message is not None:
        await callback.message.edit_text(
            ("✅ " if success else "❌ ") + escape(message),
            parse_mode="HTML",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:product:edit:"))
async def admin_product_edit_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 5:
        await callback.answer("درخواست ویرایش نامعتبر است.", show_alert=True)
        return

    try:
        product_id = int(parts[3])
    except ValueError:
        await callback.answer("محصول نامعتبر است.", show_alert=True)
        return

    field = parts[4]
    product = await get_product(product_id)
    if product is None:
        await callback.answer("محصول پیدا نشد.", show_alert=True)
        return

    await state.clear()

    if field == "category":
        categories = [c for c in await list_categories() if c.is_active]
        if callback.message is not None:
            await callback.message.answer(
                "دسته‌بندی جدید را انتخاب کنید:",
                reply_markup=category_choice_keyboard(
                    categories,
                    f"admin:edit_product:category:{product_id}",
                    f"admin:product:{product_id}",
                ),
            )
        await callback.answer()
        return

    await state.update_data(product_id=product_id, field=field)

    if field == "image":
        await state.set_state(ProductEditStates.waiting_image)
        prompt = "عکس جدید را ارسال کنید:"
    else:
        await state.set_state(ProductEditStates.waiting_value)
        prompts = {
            "name": "نام جدید را ارسال کنید:",
            "author": "نام نویسنده جدید را ارسال کنید:",
            "price": "قیمت جدید را وارد کنید؛ باید بیشتر از صفر باشد:",
            "stock": "موجودی جدید را به صورت عدد صفر یا بیشتر وارد کنید:",
            "description": "توضیحات جدید را ارسال کنید:",
        }
        prompt = prompts.get(field, "مقدار جدید را ارسال کنید:")

    if callback.message is not None:
        await callback.message.answer(
            prompt,
            reply_markup=form_navigation(
                f"admin:product:{product_id}",
                "محصول",
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:edit_product:category:"))
async def admin_product_edit_category(callback: CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 5:
        await callback.answer("درخواست نامعتبر است.", show_alert=True)
        return

    try:
        product_id = int(parts[3])
        category_id = int(parts[4])
    except ValueError:
        await callback.answer("شناسه نامعتبر است.", show_alert=True)
        return

    product, message = await update_product_field(
        product_id,
        "category_id",
        category_id,
    )
    if product is None:
        await callback.answer(message, show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            "✅ دسته‌بندی محصول تغییر کرد.",
            reply_markup=product_manage_keyboard(product),
        )
    await callback.answer()


@router.message(ProductEditStates.waiting_value)
async def admin_product_edit_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = int(data["product_id"])
    field = str(data["field"])
    raw = (message.text or "").strip()
    value = raw

    if field == "price":
        normalized = raw.replace(",", "")
        if not normalized.isdigit() or int(normalized) <= 0:
            await message.answer(
                "قیمت باید یک عدد صحیح بزرگ‌تر از صفر باشد.",
                reply_markup=form_navigation(f"admin:product:{product_id}", "محصول"),
            )
            return
        value = int(normalized)

    elif field == "stock":
        if not raw.isdigit():
            await message.answer(
                "موجودی باید عدد صحیح صفر یا بیشتر باشد.",
                reply_markup=form_navigation(f"admin:product:{product_id}", "محصول"),
            )
            return
        value = int(raw)

    elif field in {"name", "author"}:
        if len(raw) < 2:
            await message.answer(
                "مقدار واردشده خیلی کوتاه است.",
                reply_markup=form_navigation(f"admin:product:{product_id}", "محصول"),
            )
            return

    elif field == "description":
        if len(raw) < 5:
            await message.answer(
                "توضیحات خیلی کوتاه است.",
                reply_markup=form_navigation(f"admin:product:{product_id}", "محصول"),
            )
            return

    product, result_message = await update_product_field(product_id, field, value)
    if product is None:
        await message.answer(
            f"❌ {result_message}",
            reply_markup=form_navigation(f"admin:product:{product_id}", "محصول"),
        )
        return

    await state.clear()
    await message.answer(
        "✅ محصول ویرایش شد.",
        reply_markup=product_manage_keyboard(product),
    )


@router.message(ProductEditStates.waiting_image, F.photo)
async def admin_product_edit_image(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    product_id = int(data["product_id"])
    old_product = await get_product(product_id)

    if old_product is None:
        await state.clear()
        await message.answer(
            "❌ محصول پیدا نشد.",
            reply_markup=form_navigation("admin:products", "محصولات"),
        )
        return

    new_path = await save_product_photo(bot, message.photo[-1])
    product, result_message = await update_product_field(
        product_id,
        "image_path",
        new_path,
    )

    if product is None:
        remove_old_uploaded_image(new_path)
        await message.answer(
            f"❌ {result_message}",
            reply_markup=form_navigation(f"admin:product:{product_id}", "محصول"),
        )
        return

    remove_old_uploaded_image(old_product.image_path)
    await state.clear()
    await message.answer(
        "✅ تصویر محصول تغییر کرد.",
        reply_markup=product_manage_keyboard(product),
    )


@router.message(ProductEditStates.waiting_image)
async def admin_product_edit_image_fallback(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = int(data["product_id"])
    await message.answer(
        "لطفاً عکس جدید را ارسال کنید.",
        reply_markup=form_navigation(f"admin:product:{product_id}", "محصول"),
    )


async def show_product_detail(target_message, product) -> None:
    category_status = "فعال" if product.category_active else "غیرفعال ⚠️"
    product_status = "فعال ✅" if product.is_active else "غیرفعال ⛔"
    text = (
        f"📚 <b>#{product.id} {escape(product.name)}</b>\n"
        f"✍️ {escape(product.author)}\n"
        f"🗂 {escape(product.category_name)} ({category_status})\n"
        f"💰 {format_price(product.price)}\n"
        f"📦 موجودی: {product.stock}\n"
        f"وضعیت محصول: {product_status}\n\n"
        f"{escape(product.description)}"
    )
    await target_message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=product_manage_keyboard(product),
    )


@router.callback_query(F.data.startswith("admin:product:"))
async def admin_product_detail(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        return

    try:
        product_id = int(parts[2])
    except ValueError:
        await callback.answer("محصول نامعتبر است.", show_alert=True)
        return

    await state.clear()
    product = await get_product(product_id)
    if product is None:
        await callback.answer("محصول پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await show_product_detail(callback.message, product)
    await callback.answer()


# ------------------------------------------------------------------
# Orders
# ------------------------------------------------------------------

async def _show_orders_list(callback: CallbackQuery, archived: bool) -> None:
    orders = await list_latest_orders(archived=archived)
    title = "🗄 <b>سفارش‌های آرشیوشده</b>" if archived else "📦 <b>آخرین سفارش‌ها</b>"
    if not orders:
        title += "\n\nموردی وجود ندارد."

    if callback.message is not None:
        await callback.message.edit_text(
            title,
            parse_mode="HTML",
            reply_markup=admin_orders_keyboard(orders, archived=archived),
        )


@router.callback_query(F.data == "admin:orders")
async def admin_orders(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _show_orders_list(callback, archived=False)
    await callback.answer()


@router.callback_query(F.data == "admin:orders:archived")
async def admin_archived_orders(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _show_orders_list(callback, archived=True)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:status:"))
async def admin_order_status(callback: CallbackQuery, bot: Bot) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 5:
        await callback.answer("درخواست نامعتبر است.", show_alert=True)
        return

    try:
        order_id = int(parts[3])
    except ValueError:
        await callback.answer("سفارش نامعتبر است.", show_alert=True)
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

    suffix = "" if notified else "؛ پیام کاربر ارسال نشد"
    await callback.answer(f"وضعیت تغییر کرد{suffix}")


@router.callback_query(F.data.startswith("admin:order:archive:"))
async def admin_order_archive_confirm(callback: CallbackQuery) -> None:
    try:
        order_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("سفارش نامعتبر است.", show_alert=True)
        return

    order = await get_admin_order(order_id)
    if order is None:
        await callback.answer("سفارش پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            f"🗑 سفارش #{order_id} از لیست مدیریت حذف شود؟\n\n"
            "برای حفظ سابقه خرید، سفارش به‌صورت امن آرشیو می‌شود و از دیتابیس پاک نمی‌شود.",
            reply_markup=order_archive_confirmation_keyboard(order_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:archive_yes:"))
async def admin_order_archive_yes(callback: CallbackQuery) -> None:
    try:
        order_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("سفارش نامعتبر است.", show_alert=True)
        return

    order, message = await set_order_archived(order_id, True)
    if order is None:
        await callback.answer(message, show_alert=True)
        return

    if callback.message is not None:
        await show_admin_order(callback.message, order)
    await callback.answer("سفارش آرشیو شد.")


@router.callback_query(F.data.startswith("admin:order:restore:"))
async def admin_order_restore(callback: CallbackQuery) -> None:
    try:
        order_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("سفارش نامعتبر است.", show_alert=True)
        return

    order, message = await set_order_archived(order_id, False)
    if order is None:
        await callback.answer(message, show_alert=True)
        return

    if callback.message is not None:
        await show_admin_order(callback.message, order)
    await callback.answer("سفارش بازگردانده شد.")


@router.callback_query(F.data.startswith("admin:order:"))
async def admin_order_detail(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        return

    try:
        order_id = int(parts[2])
    except ValueError:
        await callback.answer("سفارش نامعتبر است.", show_alert=True)
        return

    await state.clear()
    order = await get_admin_order(order_id)
    if order is None:
        await callback.answer("سفارش پیدا نشد.", show_alert=True)
        return

    if callback.message is not None:
        await show_admin_order(callback.message, order)
    await callback.answer()


async def show_admin_order(target_message, order) -> None:
    archive_text = "\n🗄 این سفارش آرشیو شده است." if order.is_archived else ""
    lines = [
        f"📦 <b>سفارش #{order.order_id}</b>",
        f"📌 وضعیت: <b>{escape(status_label(order.status))}</b>{archive_text}",
        f"Telegram User ID: <code>{order.telegram_user_id}</code>",
        f"🕒 تاریخ: {escape(order.created_at_text)}",
        "",
        f"👤 {escape(order.customer_name)}",
        f"📞 {escape(order.phone)}",
        f"📍 {escape(order.address)}",
        "",
        "📚 <b>اقلام:</b>",
    ]

    for item in order.items:
        lines.append(
            f"• {escape(item.product_name)} × {item.quantity} = {format_price(item.subtotal)}"
        )

    lines.extend(["", f"💰 <b>مبلغ کل: {format_price(order.total_amount)}</b>"])

    await target_message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=admin_order_detail_keyboard(order),
    )
