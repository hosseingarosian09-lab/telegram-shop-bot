from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, func, select

from app.config import ROOT_DIR
from app.database.admin_repository import (
    get_all_categories,
    get_all_products,
    get_category_any,
    get_product_any,
)
from app.database.models import CartItem, Category, OrderItem, Product
from app.database.session import SessionFactory


DEFAULT_COVER_PATH = "assets/covers/default_book.png"


@dataclass(frozen=True)
class AdminCategory:
    id: int
    name: str
    is_active: bool


@dataclass(frozen=True)
class AdminProduct:
    id: int
    category_id: int
    category_name: str
    category_active: bool
    name: str
    author: str
    price: int
    stock: int
    description: str
    image_path: str
    is_active: bool


def _category_view(category: Category) -> AdminCategory:
    return AdminCategory(
        id=category.id,
        name=category.name,
        is_active=category.is_active,
    )


def _product_view(product: Product, category: Category | None) -> AdminProduct:
    return AdminProduct(
        id=product.id,
        category_id=product.category_id,
        category_name=category.name if category else "دسته‌بندی نامشخص",
        category_active=bool(category and category.is_active),
        name=product.name,
        author=product.author,
        price=product.price,
        stock=product.stock,
        description=product.description,
        image_path=product.image_path,
        is_active=product.is_active,
    )


async def _category_name_exists(
    session,
    name: str,
    exclude_id: int | None = None,
) -> bool:
    statement = select(Category.id).where(
        func.lower(Category.name) == name.strip().lower()
    )
    if exclude_id is not None:
        statement = statement.where(Category.id != exclude_id)

    return await session.scalar(statement) is not None


async def list_categories() -> list[AdminCategory]:
    async with SessionFactory() as session:
        categories = await get_all_categories(session)

    return [_category_view(category) for category in categories]


async def get_category(category_id: int) -> AdminCategory | None:
    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)
        return _category_view(category) if category else None


async def add_category(name: str) -> tuple[AdminCategory | None, str]:
    clean_name = name.strip()

    async with SessionFactory() as session:
        if await _category_name_exists(session, clean_name):
            return None, "دسته‌بندی با این نام از قبل وجود دارد."

        category = Category(
            name=clean_name,
            slug=f"category-{uuid4().hex}",
            is_active=True,
        )
        session.add(category)
        await session.flush()
        category.slug = f"category-{category.id}"
        await session.commit()
        await session.refresh(category)

        return _category_view(category), "دسته‌بندی ساخته شد."


async def rename_category(
    category_id: int,
    name: str,
) -> tuple[AdminCategory | None, str]:
    clean_name = name.strip()

    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)
        if category is None:
            return None, "دسته‌بندی پیدا نشد."

        if await _category_name_exists(session, clean_name, exclude_id=category_id):
            return None, "دسته‌بندی دیگری با این نام وجود دارد."

        category.name = clean_name
        await session.commit()
        await session.refresh(category)
        return _category_view(category), "نام دسته‌بندی تغییر کرد."


async def toggle_category(category_id: int) -> AdminCategory | None:
    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)
        if category is None:
            return None

        category.is_active = not category.is_active
        await session.commit()
        await session.refresh(category)
        return _category_view(category)


async def delete_category(category_id: int) -> tuple[bool, str]:
    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)
        if category is None:
            return False, "دسته‌بندی پیدا نشد."

        product_count = await session.scalar(
            select(func.count(Product.id)).where(
                Product.category_id == category_id
            )
        )
        if int(product_count or 0) > 0:
            return (
                False,
                "این دسته‌بندی هنوز محصول دارد. ابتدا محصولات را جابه‌جا یا حذف کنید.",
            )

        await session.delete(category)
        await session.commit()
        return True, "دسته‌بندی حذف شد."


async def list_products() -> list[AdminProduct]:
    async with SessionFactory() as session:
        products = await get_all_products(session)
        categories = {
            category.id: category
            for category in await get_all_categories(session)
        }

    return [
        _product_view(product, categories.get(product.category_id))
        for product in products
    ]


async def get_product(product_id: int) -> AdminProduct | None:
    async with SessionFactory() as session:
        product = await get_product_any(session, product_id)
        if product is None:
            return None

        category = await get_category_any(session, product.category_id)
        return _product_view(product, category)


async def create_product(
    category_id: int,
    name: str,
    author: str,
    price: int,
    stock: int,
    description: str,
    image_path: str | None,
) -> tuple[AdminProduct | None, str]:
    if price <= 0:
        return None, "قیمت باید بیشتر از صفر باشد."
    if stock < 0:
        return None, "موجودی نمی‌تواند منفی باشد."

    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)
        if category is None or not category.is_active:
            return None, "دسته‌بندی انتخاب‌شده فعال نیست."

        product = Product(
            category_id=category_id,
            name=name.strip(),
            author=author.strip(),
            price=price,
            stock=stock,
            description=description.strip(),
            image_path=image_path or DEFAULT_COVER_PATH,
            is_active=True,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return _product_view(product, category), "محصول ساخته شد."


async def update_product_field(
    product_id: int,
    field: str,
    value,
) -> tuple[AdminProduct | None, str]:
    allowed_fields = {
        "name",
        "author",
        "price",
        "stock",
        "description",
        "category_id",
        "image_path",
    }
    if field not in allowed_fields:
        return None, "فیلد ویرایش نامعتبر است."

    if field == "price" and int(value) <= 0:
        return None, "قیمت باید بیشتر از صفر باشد."
    if field == "stock" and int(value) < 0:
        return None, "موجودی نمی‌تواند منفی باشد."

    async with SessionFactory() as session:
        product = await get_product_any(session, product_id)
        if product is None:
            return None, "محصول پیدا نشد."

        if field == "category_id":
            category = await get_category_any(session, int(value))
            if category is None or not category.is_active:
                return None, "دسته‌بندی انتخاب‌شده فعال نیست."

        setattr(product, field, value)
        await session.commit()
        await session.refresh(product)
        category = await get_category_any(session, product.category_id)
        return _product_view(product, category), "محصول ویرایش شد."


async def toggle_product(product_id: int) -> AdminProduct | None:
    async with SessionFactory() as session:
        product = await get_product_any(session, product_id)
        if product is None:
            return None

        product.is_active = not product.is_active
        await session.commit()
        await session.refresh(product)
        category = await get_category_any(session, product.category_id)
        return _product_view(product, category)


async def delete_product(product_id: int) -> tuple[str, str]:
    """Safely delete a product.

    Products already referenced by order history are preserved and deactivated
    instead of being physically removed. Products with no order history are
    deleted; stale cart rows are removed at the same time.
    """

    image_path: str | None = None

    async with SessionFactory() as session:
        product = await get_product_any(session, product_id)
        if product is None:
            return "not_found", "محصول پیدا نشد."

        order_reference_count = await session.scalar(
            select(func.count(OrderItem.id)).where(
                OrderItem.product_id == product_id
            )
        )

        if int(order_reference_count or 0) > 0:
            product.is_active = False
            await session.commit()
            return (
                "deactivated",
                "این محصول در سابقه سفارش‌ها استفاده شده و برای حفظ تاریخچه، غیرفعال شد.",
            )

        image_path = product.image_path
        await session.execute(
            delete(CartItem).where(CartItem.product_id == product_id)
        )
        await session.delete(product)
        await session.commit()

    if image_path:
        remove_old_uploaded_image(image_path)

    return "deleted", "محصول برای همیشه حذف شد."


def remove_old_uploaded_image(image_path: str) -> None:
    normalized = image_path.replace("\\", "/")
    if not normalized.startswith("assets/uploads/"):
        return

    absolute = Path(ROOT_DIR) / normalized
    try:
        absolute.unlink(missing_ok=True)
    except OSError:
        pass
