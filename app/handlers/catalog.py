from html import escape
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.config import ROOT_DIR
from app.database.repository import get_active_categories, get_category, get_product, get_products_by_category
from app.database.session import SessionFactory
from app.keyboards.catalog import categories_keyboard, product_detail_keyboard, products_keyboard

router = Router(name="catalog")


def format_price(price: int) -> str:
    return f"{price:,} تومان"


async def send_categories(message: Message) -> None:
    async with SessionFactory() as session:
        categories = await get_active_categories(session)
    if not categories:
        await message.answer("فعلاً دسته‌بندی فعالی وجود ندارد.")
        return
    await message.answer("📚 دسته‌بندی کتاب‌ها:", reply_markup=categories_keyboard(categories))


@router.message(F.text == "🛍 محصولات")
async def products_menu_handler(message: Message) -> None:
    await send_categories(message)


@router.callback_query(F.data == "catalog:categories")
async def categories_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer(); return
    async with SessionFactory() as session:
        categories = await get_active_categories(session)
    if not categories:
        await callback.answer("دسته‌بندی فعالی وجود ندارد.", show_alert=True); return
    if callback.message.photo:
        await callback.message.delete()
        await callback.bot.send_message(callback.message.chat.id, "📚 دسته‌بندی کتاب‌ها:", reply_markup=categories_keyboard(categories))
    else:
        await callback.message.edit_text("📚 دسته‌بندی کتاب‌ها:", reply_markup=categories_keyboard(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def category_callback(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer(); return
    try:
        category_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("دسته‌بندی نامعتبر است.", show_alert=True); return
    async with SessionFactory() as session:
        category = await get_category(session, category_id)
        if category is None:
            await callback.answer("این دسته‌بندی پیدا نشد.", show_alert=True); return
        products = await get_products_by_category(session, category_id)
    if not products:
        await callback.answer("این دسته‌بندی فعلاً کتابی ندارد.", show_alert=True); return
    text = f"{escape(category.name)}\n\nیک کتاب را انتخاب کنید:"
    if callback.message.photo:
        await callback.message.delete()
        await callback.bot.send_message(callback.message.chat.id, text, reply_markup=products_keyboard(products))
    else:
        await callback.message.edit_text(text, reply_markup=products_keyboard(products))
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def product_callback(callback: CallbackQuery, bot: Bot) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer(); return
    try:
        product_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("کتاب نامعتبر است.", show_alert=True); return
    async with SessionFactory() as session:
        product = await get_product(session, product_id)
    if product is None:
        await callback.answer("این کتاب پیدا نشد.", show_alert=True); return
    stock_text = f"{product.stock} عدد" if product.stock > 0 else "ناموجود"
    caption = (
        f"<b>{escape(product.name)}</b>\n"
        f"✍️ {escape(product.author)}\n\n"
        f"💰 {format_price(product.price)}\n"
        f"📦 موجودی: {stock_text}\n\n"
        f"{escape(product.description)}"
    )
    image_path = Path(ROOT_DIR) / product.image_path
    await callback.message.delete()
    if image_path.exists():
        await bot.send_photo(callback.message.chat.id, FSInputFile(image_path), caption=caption, parse_mode="HTML", reply_markup=product_detail_keyboard(product.category_id))
    else:
        await bot.send_message(callback.message.chat.id, caption, parse_mode="HTML", reply_markup=product_detail_keyboard(product.category_id))
    await callback.answer()
