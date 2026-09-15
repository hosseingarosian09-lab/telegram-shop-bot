import logging

from sqlalchemy import text

from app.database.session import engine


logger = logging.getLogger(__name__)


async def _column_names(connection, table_name: str) -> set[str]:
    result = await connection.execute(text(f"PRAGMA table_info({table_name})"))
    return {str(row[1]) for row in result.fetchall()}


async def migrate_database() -> None:
    """Apply the tiny SQLite migrations used by this portfolio project.

    This intentionally avoids a full migration framework. It keeps existing V1
    databases compatible while fresh databases still get the complete schema
    directly from SQLAlchemy models.
    """

    async with engine.begin() as connection:
        order_columns = await _column_names(connection, "orders")

        if "is_archived" not in order_columns:
            await connection.execute(
                text(
                    "ALTER TABLE orders "
                    "ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            logger.info("Database migration: added orders.is_archived")

        if "stock_restored" not in order_columns:
            await connection.execute(
                text(
                    "ALTER TABLE orders "
                    "ADD COLUMN stock_restored BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            logger.info("Database migration: added orders.stock_restored")

        # Earlier versions did not restore stock when an order was cancelled.
        # Any legacy cancelled order with stock_restored=0 is repaired once.
        legacy_cancelled = await connection.execute(
            text(
                """
                SELECT oi.product_id, SUM(oi.quantity) AS quantity
                FROM orders AS o
                JOIN order_items AS oi ON oi.order_id = o.id
                WHERE o.status = 'cancelled'
                  AND COALESCE(o.stock_restored, 0) = 0
                GROUP BY oi.product_id
                """
            )
        )
        restored_any = False
        for product_id, quantity in legacy_cancelled.fetchall():
            await connection.execute(
                text(
                    "UPDATE products "
                    "SET stock = stock + :quantity "
                    "WHERE id = :product_id"
                ),
                {"quantity": int(quantity), "product_id": int(product_id)},
            )
            restored_any = True

        if restored_any:
            await connection.execute(
                text(
                    "UPDATE orders SET stock_restored = 1 "
                    "WHERE status = 'cancelled' "
                    "AND COALESCE(stock_restored, 0) = 0"
                )
            )
            logger.info("Database migration: repaired stock for legacy cancelled orders")

        # Existing SQLite databases cannot gain CHECK constraints through a
        # simple ALTER TABLE. These triggers enforce the same rules for both
        # legacy and fresh databases.
        trigger_statements = [
            """
            CREATE TRIGGER IF NOT EXISTS trg_products_price_insert
            BEFORE INSERT ON products
            WHEN NEW.price <= 0
            BEGIN
                SELECT RAISE(ABORT, 'product price must be positive');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_products_price_update
            BEFORE UPDATE OF price ON products
            WHEN NEW.price <= 0
            BEGIN
                SELECT RAISE(ABORT, 'product price must be positive');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_products_stock_insert
            BEFORE INSERT ON products
            WHEN NEW.stock < 0
            BEGIN
                SELECT RAISE(ABORT, 'product stock cannot be negative');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_products_stock_update
            BEFORE UPDATE OF stock ON products
            WHEN NEW.stock < 0
            BEGIN
                SELECT RAISE(ABORT, 'product stock cannot be negative');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_cart_quantity_insert
            BEFORE INSERT ON cart_items
            WHEN NEW.quantity <= 0
            BEGIN
                SELECT RAISE(ABORT, 'cart quantity must be positive');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_cart_quantity_update
            BEFORE UPDATE OF quantity ON cart_items
            WHEN NEW.quantity <= 0
            BEGIN
                SELECT RAISE(ABORT, 'cart quantity must be positive');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_order_item_price_insert
            BEFORE INSERT ON order_items
            WHEN NEW.unit_price <= 0
            BEGIN
                SELECT RAISE(ABORT, 'order item price must be positive');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_order_item_quantity_insert
            BEFORE INSERT ON order_items
            WHEN NEW.quantity <= 0
            BEGIN
                SELECT RAISE(ABORT, 'order item quantity must be positive');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_order_status_insert
            BEFORE INSERT ON orders
            WHEN NEW.status NOT IN ('pending', 'confirmed', 'shipped', 'completed', 'cancelled')
            BEGIN
                SELECT RAISE(ABORT, 'invalid order status');
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_order_status_update
            BEFORE UPDATE OF status ON orders
            WHEN NEW.status NOT IN ('pending', 'confirmed', 'shipped', 'completed', 'cancelled')
            BEGIN
                SELECT RAISE(ABORT, 'invalid order status');
            END
            """,
        ]

        for statement in trigger_statements:
            await connection.execute(text(statement))

        duplicate_category = (
            await connection.execute(
                text(
                    "SELECT name FROM categories "
                    "GROUP BY name HAVING COUNT(*) > 1 LIMIT 1"
                )
            )
        ).first()
        if duplicate_category is None:
            await connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    "uq_categories_name_existing ON categories(name)"
                )
            )
        else:
            logger.warning(
                "Duplicate category names exist; unique category-name index was skipped."
            )

        invalid_row = (
            await connection.execute(
                text(
                    """
                    SELECT 'products' AS source, id
                    FROM products
                    WHERE price <= 0 OR stock < 0
                    UNION ALL
                    SELECT 'cart_items', id
                    FROM cart_items
                    WHERE quantity <= 0
                    UNION ALL
                    SELECT 'order_items', id
                    FROM order_items
                    WHERE unit_price <= 0 OR quantity <= 0
                    LIMIT 1
                    """
                )
            )
        ).first()
        if invalid_row is not None:
            raise RuntimeError(
                f"Invalid legacy database data found in {invalid_row[0]} row {invalid_row[1]}."
            )

        foreign_key_issue = (
            await connection.execute(text("PRAGMA foreign_key_check"))
        ).first()
        if foreign_key_issue is not None:
            raise RuntimeError(
                "Database foreign-key integrity check failed. "
                "Back up data/shop.db before continuing."
            )
