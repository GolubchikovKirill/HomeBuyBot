from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Мой список", callback_data="view_list")],
        [InlineKeyboardButton(text="➕ Добавить продукт", callback_data="add_product")],
        [InlineKeyboardButton(text="🤖 AI помощник", callback_data="ai_help")],
        [InlineKeyboardButton(text="🧹 Очистить список", callback_data="clear_options")]
    ])


def get_list_actions() -> InlineKeyboardMarkup:
    """Действия со списком"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить продукт", callback_data="add_product")],
        [InlineKeyboardButton(text="✅ Отметить товары", callback_data="mark_products")],
        [InlineKeyboardButton(text="🗑 Управление товарами", callback_data="manage_products")],
        [InlineKeyboardButton(text="🧹 Очистить список", callback_data="clear_options")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")]
    ])


def get_product_list_keyboard(products) -> InlineKeyboardMarkup:
    """НОВОЕ: Клавиатура для отметки продуктов в списке"""
    keyboard = []

    for product in products:
        status_emoji = "✅" if product['is_bought'] else "🔘"
        button_text = f"{status_emoji} {product['name']}"
        if product['quantity'] != '1':
            button_text += f" ({product['quantity']})"

        # Кнопка для переключения статуса
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"toggle_{product['id']}"
            )
        ])

    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="✅ Отметить товары", callback_data="mark_products"),
        InlineKeyboardButton(text="🗑 Управление", callback_data="manage_products")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🧹 Очистить список", callback_data="clear_options")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_mark_products_keyboard(products) -> InlineKeyboardMarkup:
    """НОВОЕ: Специальная клавиатура для отметки товаров"""
    keyboard = []

    for product in products:
        if product['is_bought']:
            button_text = f"✅ {product['name']}"
            action_text = "Снять отметку"
        else:
            button_text = f"🔘 {product['name']}"
            action_text = "Отметить"

        if product['quantity'] != '1':
            button_text += f" ({product['quantity']})"

        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"toggle_{product['id']}"
            )
        ])

    # Кнопки быстрых действий
    keyboard.append([
        InlineKeyboardButton(text="✅ Отметить все", callback_data="mark_all"),
        InlineKeyboardButton(text="🔘 Снять все", callback_data="unmark_all")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ К списку", callback_data="view_list")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_clear_options() -> InlineKeyboardMarkup:
    """Опции очистки списка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Только купленные", callback_data="clear_bought")],
        [InlineKeyboardButton(text="🗑 Весь список", callback_data="clear_all")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="view_list")]
    ])


def get_back_to_menu() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")]
    ])


def get_product_management_keyboard(products) -> InlineKeyboardMarkup:
    """Клавиатура для управления продуктами"""
    keyboard = []

    for product in products:
        status_emoji = "✅" if product['is_bought'] else "🔘"
        button_text = f"{status_emoji} {product['name'][:20]}"

        # Кнопки в ряд: статус и удаление
        row = [
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"toggle_{product['id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"delete_{product['id']}"
            )
        ]
        keyboard.append(row)

    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="🧹 Очистить список", callback_data="clear_options")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ К списку", callback_data="view_list")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ai_actions_keyboard(suggested_products: List[Dict], intent: str) -> InlineKeyboardMarkup:
    """Клавиатура с действиями после ответа AI"""
    keyboard = []

    if suggested_products:
        products_data = "_".join([str(i) for i in range(len(suggested_products))])
        keyboard.append([
            InlineKeyboardButton(
                text=f"➕ Добавить все продукты ({len(suggested_products)})",
                callback_data=f"add_ai_products_{products_data}"
            )
        ])

    if intent == "recipe":
        keyboard.append([
            InlineKeyboardButton(text="📋 Посмотреть список", callback_data="view_list"),
            InlineKeyboardButton(text="🤖 Еще рецепт", callback_data="ai_help")
        ])
    elif intent == "shopping":
        keyboard.append([
            InlineKeyboardButton(text="📝 Мой список", callback_data="view_list"),
            InlineKeyboardButton(text="➕ Добавить вручную", callback_data="add_product")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="📝 Мой список", callback_data="view_list"),
            InlineKeyboardButton(text="🤖 Еще вопрос", callback_data="ai_help")
        ])

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ai_chat_keyboard(suggested_products: List[Dict] = None, intent: str = "general") -> InlineKeyboardMarkup:
    """Клавиатура для AI-чата"""
    keyboard = []

    # Если AI предложил продукты
    if suggested_products and len(suggested_products) > 0:
        products_data = "_".join([str(i) for i in range(len(suggested_products))])
        keyboard.append([
            InlineKeyboardButton(
                text=f"➕ Добавить продукты ({len(suggested_products)})",
                callback_data=f"add_ai_products_{products_data}"
            )
        ])

    # Быстрые действия в зависимости от намерения
    if intent == "recipe":
        keyboard.append([
            InlineKeyboardButton(text="🍳 Еще рецепт", callback_data="ai_help"),
            InlineKeyboardButton(text="📝 Мой список", callback_data="view_list")
        ])
    elif intent == "shopping":
        keyboard.append([
            InlineKeyboardButton(text="📝 Посмотреть список", callback_data="view_list"),
            InlineKeyboardButton(text="➕ Добавить вручную", callback_data="add_product")
        ])
    elif intent == "welcome":
        keyboard.append([
            InlineKeyboardButton(text="📝 Мой список", callback_data="view_list"),
            InlineKeyboardButton(text="➕ Добавить продукт", callback_data="add_product")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="📝 Мой список", callback_data="view_list"),
            InlineKeyboardButton(text="➕ Добавить продукт", callback_data="add_product")
        ])

    # Кнопки выхода и справки
    keyboard.append([
        InlineKeyboardButton(text="📋 Главное меню", callback_data="exit_ai_chat"),
        InlineKeyboardButton(text="ℹ️ Справка", callback_data="ai_help_info")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
