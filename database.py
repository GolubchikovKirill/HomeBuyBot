import aiosqlite
from typing import List, Optional, Dict
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)


async def init_db():
    """Инициализация базы данных с таблицами"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            # Включаем поддержку внешних ключей
            await db.execute('PRAGMA foreign_keys = ON')

            # Таблица пользователей
            await db.execute('''
                             CREATE TABLE IF NOT EXISTS users
                             (
                                 user_id    INTEGER PRIMARY KEY,
                                 username   TEXT,
                                 first_name TEXT,
                                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                             )
                             ''')

            # Таблица списков покупок
            await db.execute('''
                             CREATE TABLE IF NOT EXISTS shopping_lists
                             (
                                 id         INTEGER PRIMARY KEY AUTOINCREMENT,
                                 user_id    INTEGER NOT NULL,
                                 name       TEXT      DEFAULT 'Основной список',
                                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                             )
                             ''')

            # Таблица продуктов
            await db.execute('''
                             CREATE TABLE IF NOT EXISTS products
                             (
                                 id        INTEGER PRIMARY KEY AUTOINCREMENT,
                                 list_id   INTEGER NOT NULL,
                                 name      TEXT    NOT NULL,
                                 quantity  TEXT      DEFAULT '1',
                                 is_bought INTEGER   DEFAULT 0,
                                 added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                 FOREIGN KEY (list_id) REFERENCES shopping_lists (id) ON DELETE CASCADE
                             )
                             ''')

            await db.commit()
            logger.info("✅ База данных инициализирована")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise


class Database:
    @staticmethod
    async def add_user(user_id: int, username: str = None, first_name: str = None):
        """Добавить пользователя в систему"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # Проверяем, существует ли пользователь
                cursor = await db.execute(
                    'SELECT user_id FROM users WHERE user_id = ?',
                    (user_id,)
                )
                existing_user = await cursor.fetchone()

                if not existing_user:
                    await db.execute(
                        'INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
                        (user_id, username or '', first_name or 'Пользователь')
                    )
                    await db.commit()
                    logger.info(f"👤 Пользователь {user_id} добавлен")

        except Exception as e:
            logger.error(f"❌ Ошибка добавления пользователя: {e}")

    @staticmethod
    async def get_or_create_list(user_id: int, list_name: str = 'Основной список') -> Optional[int]:
        """Получить или создать список покупок"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # Проверяем существующий список
                cursor = await db.execute(
                    'SELECT id FROM shopping_lists WHERE user_id = ? AND name = ?',
                    (user_id, list_name)
                )
                result = await cursor.fetchone()

                if result:
                    return result[0]

                # Создаем новый список
                cursor = await db.execute(
                    'INSERT INTO shopping_lists (user_id, name) VALUES (?, ?)',
                    (user_id, list_name)
                )
                await db.commit()
                list_id = cursor.lastrowid
                logger.info(f"📝 Создан список '{list_name}' для пользователя {user_id}")
                return list_id

        except Exception as e:
            logger.error(f"❌ Ошибка работы со списком: {e}")
            return None

    @staticmethod
    async def add_product(list_id: int, name: str, quantity: str = '1'):
        """Добавить продукт в список"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                await db.execute(
                    'INSERT INTO products (list_id, name, quantity, is_bought) VALUES (?, ?, ?, 0)',
                    (list_id, name.strip(), quantity.strip())
                )
                await db.commit()
                logger.info(f"➕ Добавлен продукт: {name} ({quantity})")

        except Exception as e:
            logger.error(f"❌ Ошибка добавления продукта: {e}")

    @staticmethod
    async def get_products(list_id: int) -> List[Dict]:
        """Получить все продукты из списка"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute(
                    'SELECT id, name, quantity, is_bought FROM products WHERE list_id = ? ORDER BY is_bought ASC, added_at DESC',
                    (list_id,)
                )
                products = await cursor.fetchall()

                return [
                    {
                        'id': p[0],
                        'name': p[1],
                        'quantity': p[2],
                        'is_bought': bool(p[3])
                    }
                    for p in products
                ]

        except Exception as e:
            logger.error(f"❌ Ошибка получения продуктов: {e}")
            return []

    @staticmethod
    async def toggle_product_bought(product_id: int) -> bool:
        """Переключить статус покупки продукта"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # Получаем текущий статус
                cursor = await db.execute(
                    'SELECT is_bought FROM products WHERE id = ?',
                    (product_id,)
                )
                result = await cursor.fetchone()

                if result:
                    new_status = 1 if result[0] == 0 else 0
                    await db.execute(
                        'UPDATE products SET is_bought = ? WHERE id = ?',
                        (new_status, product_id)
                    )
                    await db.commit()
                    logger.info(f"🔄 Изменен статус продукта {product_id} на {bool(new_status)}")
                    return True

                return False

        except Exception as e:
            logger.error(f"❌ Ошибка изменения статуса: {e}")
            return False

    @staticmethod
    async def delete_product(product_id: int) -> bool:
        """Удалить продукт из списка"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute(
                    'DELETE FROM products WHERE id = ?',
                    (product_id,)
                )
                await db.commit()

                if cursor.rowcount > 0:
                    logger.info(f"🗑 Удален продукт {product_id}")
                    return True
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка удаления продукта: {e}")
            return False

    @staticmethod
    async def clear_bought_products(list_id: int) -> int:
        """Удалить все купленные продукты"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute(
                    'DELETE FROM products WHERE list_id = ? AND is_bought = 1',
                    (list_id,)
                )
                await db.commit()
                deleted_count = cursor.rowcount
                logger.info(f"🧹 Удалено {deleted_count} купленных товаров")
                return deleted_count

        except Exception as e:
            logger.error(f"❌ Ошибка очистки купленных товаров: {e}")
            return 0

    @staticmethod
    async def get_user_stats(user_id: int) -> Dict:
        """Получить статистику пользователя"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # Считаем общее количество продуктов
                cursor = await db.execute('''
                                          SELECT COUNT(*)                                       as total_products,
                                                 SUM(CASE WHEN is_bought = 1 THEN 1 ELSE 0 END) as bought_products
                                          FROM products p
                                                   JOIN shopping_lists sl ON p.list_id = sl.id
                                          WHERE sl.user_id = ?
                                          ''', (user_id,))

                stats = await cursor.fetchone()

                return {
                    'total_products': stats[0] or 0,
                    'bought_products': stats[1] or 0,
                    'remaining_products': (stats[0] or 0) - (stats[1] or 0)
                }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {'total_products': 0, 'bought_products': 0, 'remaining_products': 0}
