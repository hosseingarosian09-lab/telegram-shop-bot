from dataclasses import dataclass
from pathlib import Path

from app.config import ROOT_DIR
from app.database.admin_repository import (
    get_all_categories,
    get_all_products,
    get_category_any,
    get_product_any,
)
from app.database.models import Category, Product
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
    name: str
    author: str
    price: int
    stock: int
    description: str
    image_path: str
    is_active: bool


async def list_categories() -> list[AdminCategory]:
    async with SessionFactory() as session:
        categories = await get_all_categories(session)

    return [
        AdminCategory(
            id=category.id,
            name=category.name,
            is_active=category.is_active,
        )
        for category in categories
    ]


async def get_category(category_id: int) -> AdminCategory | None:
    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)

        if category is None:
            return None

        return AdminCategory(
            id=category.id,
            name=category.name,
            is_active=category.is_active,
        )


async def add_category(name: str) -> AdminCategory:
    async with SessionFactory() as session:
        category = Category(
            name=name.strip(),
            slug=f"category-{id(name)}",
            is_active=True,
        )
        session.add(category)
        await session.flush()

        # Replace temporary slug with stable DB-based slug.
        category.slug = f"category-{category.id}"
        await session.commit()
        await session.refresh(category)

        return AdminCategory(
            id=category.id,
            name=category.name,
            is_active=category.is_active,
        )


async def rename_category(
    category_id: int,
    name: str,
) -> bool:
    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)

        if category is None:
            return False

        category.name = name.strip()
        await session.commit()
        return True


async def toggle_category(category_id: int) -> AdminCategory | None:
    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)

        if category is None:
            return None

        category.is_active = not category.is_active
        await session.commit()
        await session.refresh(category)

        return AdminCategory(
            id=category.id,
            name=category.name,
            is_active=category.is_active,
        )


async def list_products() -> list[AdminProduct]:
    async with SessionFactory() as session:
        products = await get_all_products(session)
        categories = {
            category.id: category.name
            for category in await get_all_categories(session)
        }

    return [
        AdminProduct(
            id=product.id,
            category_id=product.category_id,
            category_name=categories.get(product.category_id, "Unknown"),
            name=product.name,
            author=product.author,
            price=product.price,
            stock=product.stock,
            description=product.description,
            image_path=product.image_path,
            is_active=product.is_active,
        )
        for product in products
    ]


async def get_product(product_id: int) -> AdminProduct | None:
    async with SessionFactory() as session:
        product = await get_product_any(session, product_id)

        if product is None:
            return None

        category = await get_category_any(session, product.category_id)
        category_name = category.name if category else "Unknown"

        return AdminProduct(
            id=product.id,
            category_id=product.category_id,
            category_name=category_name,
            name=product.name,
            author=product.author,
            price=product.price,
            stock=product.stock,
            description=product.description,
            image_path=product.image_path,
            is_active=product.is_active,
        )


async def create_product(
    category_id: int,
    name: str,
    author: str,
    price: int,
    stock: int,
    description: str,
    image_path: str | None,
) -> AdminProduct | None:
    async with SessionFactory() as session:
        category = await get_category_any(session, category_id)

        if category is None:
            return None

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

        return AdminProduct(
            id=product.id,
            category_id=product.category_id,
            category_name=category.name,
            name=product.name,
            author=product.author,
            price=product.price,
            stock=product.stock,
            description=product.description,
            image_path=product.image_path,
            is_active=product.is_active,
        )


async def update_product_field(
    product_id: int,
    field: str,
    value,
) -> bool:
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
        return False

    async with SessionFactory() as session:
        product = await get_product_any(session, product_id)

        if product is None:
            return False

        if field == "category_id":
            category = await get_category_any(session, int(value))
            if category is None:
                return False

        setattr(product, field, value)
        await session.commit()
        return True


async def toggle_product(product_id: int) -> AdminProduct | None:
    async with SessionFactory() as session:
        product = await get_product_any(session, product_id)

        if product is None:
            return None

        product.is_active = not product.is_active
        await session.commit()
        await session.refresh(product)

        category = await get_category_any(session, product.category_id)

        return AdminProduct(
            id=product.id,
            category_id=product.category_id,
            category_name=category.name if category else "Unknown",
            name=product.name,
            author=product.author,
            price=product.price,
            stock=product.stock,
            description=product.description,
            image_path=product.image_path,
            is_active=product.is_active,
        )


def remove_old_uploaded_image(image_path: str) -> None:
    normalized = image_path.replace("\\", "/")

    if not normalized.startswith("assets/uploads/"):
        return

    absolute = Path(ROOT_DIR) / normalized

    try:
        absolute.unlink(missing_ok=True)
    except OSError:
        pass
