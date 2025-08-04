#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных семейного бота
"""
import asyncio
import os
import sqlite3
from pathlib import Path
from config import DATABASE_URL


def create_database_sync():
    """Создание базы данных синхронно (для IDE)"""

    # Удаляем старую базу если есть
    if os.path.exists(DATABASE_URL):
        print(f"🗑 Удаляем существующую базу: {DATABASE_URL}")
        os.remove(DATABASE_URL)

    # Создаем новую базу
    print(f"📊 Создаем новую базу данных: {DATABASE_URL}")

    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Включаем поддержку внешних ключей
    cursor.execute('PRAGMA foreign_keys = ON')

    # Создаем таблицу пользователей
    cursor.execute('''
                   CREATE TABLE users
                   (
                       user_id    INTEGER PRIMARY KEY,
                       username   TEXT,
                       first_name TEXT,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')
    print("✅ Таблица 'users' создана")

    # Создаем таблицу списков покупок
    cursor.execute('''
                   CREATE TABLE shopping_lists
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id    INTEGER NOT NULL,
                       name       TEXT      DEFAULT 'Основной список',
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                   )
                   ''')
    print("✅ Таблица 'shopping_lists' создана")

    # Создаем таблицу продуктов
    cursor.execute('''
                   CREATE TABLE products
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
    print("✅ Таблица 'products' создана")

    # Создаем индексы для оптимизации
    cursor.execute('CREATE INDEX idx_products_list_id ON products (list_id)')
    cursor.execute('CREATE INDEX idx_products_is_bought ON products (is_bought)')
    cursor.execute('CREATE INDEX idx_shopping_lists_user_id ON shopping_lists (user_id)')
    print("✅ Индексы созданы")

    # Добавляем тестовые данные
    print("\n📋 Добавляем тестовые данные...")

    # Тестовый пользователь
    cursor.execute('''
                   INSERT INTO users (user_id, username, first_name)
                   VALUES (123456789, 'test_user', 'Тестовый пользователь')
                   ''')

    # Тестовый список
    cursor.execute('''
                   INSERT INTO shopping_lists (user_id, name)
                   VALUES (123456789, 'Основной список')
                   ''')

    # Тестовые продукты
    test_products = [
        (1, 'Молоко', '1 литр', 0),
        (1, 'Хлеб', '1 буханка', 0),
        (1, 'Яйца', '10 штук', 1),
        (1, 'Помидоры', '500 г', 0),
        (1, 'Сыр', '200 г', 1)
    ]

    cursor.executemany('''
                       INSERT INTO products (list_id, name, quantity, is_bought)
                       VALUES (?, ?, ?, ?)
                       ''', test_products)

    print("✅ Тестовые данные добавлены")

    conn.commit()
    conn.close()

    print(f"\n🎉 База данных '{DATABASE_URL}' успешно создана!")
    print_database_info()


def print_database_info():
    """Выводим информацию о созданной базе"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Информация о таблицах
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"\n📊 Информация о базе данных:")
    print(f"📁 Файл: {os.path.abspath(DATABASE_URL)}")
    print(f"📋 Таблицы: {[table[0] for table in tables]}")

    # Статистика по данным
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM shopping_lists")
    lists_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE is_bought = 1")
    bought_count = cursor.fetchone()[0]

    print(f"👥 Пользователей: {users_count}")
    print(f"📝 Списков: {lists_count}")
    print(f"🛒 Продуктов: {products_count}")
    print(f"✅ Купленных: {bought_count}")

    conn.close()


async def test_async_database():
    """Тестируем асинхронные функции"""
    from database import Database, init_db

    print("\n🧪 Тестируем асинхронные функции...")

    # Инициализируем асинхронно (проверяем совместимость)
    await init_db()

    # Тестируем функции
    test_user_id = 987654321
    await Database.add_user(test_user_id, "async_user", "Асинхронный")

    list_id = await Database.get_or_create_list(test_user_id, "Тестовый список")
    await Database.add_product(list_id, "Async продукт", "1 шт")

    products = await Database.get_products(list_id)
    print(f"✅ Асинхронный тест прошел успешно. Продуктов: {len(products)}")


def main():
    """Главная функция инициализации"""
    print("🚀 Инициализация базы данных семейного бота\n")

    # Создаем базу синхронно
    create_database_sync()

    # Тестируем асинхронные функции
    asyncio.run(test_async_database())

    print("\n✨ Инициализация завершена! Теперь можно запускать бота.")


if __name__ == "__main__":
    main()