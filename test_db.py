import asyncio
import sqlite3
from database import Database, init_db


async def test_database():
    """Тестируем работу с базой данных"""
    print("🧪 Тестируем базу данных...")

    # Инициализируем
    await init_db()

    # Тестовый пользователь
    user_id = 999999
    await Database.add_user(user_id, "test", "Тест")
    print("✅ Пользователь добавлен")

    # Создаем список
    list_id = await Database.get_or_create_list(user_id)
    print(f"✅ Список создан: {list_id}")

    # Добавляем продукты
    await Database.add_product(list_id, "Тестовый хлеб", "1 буханка")
    await Database.add_product(list_id, "Тестовое молоко", "1 литр")
    print("✅ Продукты добавлены")

    # Проверяем продукты
    products = await Database.get_products(list_id)
    print(f"📋 Найдено продуктов: {len(products)}")

    for p in products:
        print(f"  • {p['name']} ({p['quantity']}) - купен: {p['is_bought']}")

    # Проверяем через SQLite напрямую
    conn = sqlite3.connect('shopping.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    print(f"📊 Продуктов в базе (SQLite): {count}")
    conn.close()


if __name__ == "__main__":
    asyncio.run(test_database())
