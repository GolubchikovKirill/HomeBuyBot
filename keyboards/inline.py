from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Мой список", callback_data="view_list")],
        [InlineKeyboardButton(text="➕ Добавить продукт", callback_data="add_product")],
        [InlineKeyboardButton(text="🤖 AI помощник", callback_data="ai_help")],
        [InlineKeyboardButton(text="🧹 Очистить купленное", callback_data="clear_bought")]
    ])


def get_list_actions() -> InlineKeyboardMarkup:
    """Действия со списком"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить продукт", callback_data="add_product")],
        [InlineKeyboardButton(text="🗑 Управление товарами", callback_data="manage_products")],
        [InlineKeyboardButton(text="🧹 Очистить купленное", callback_data="clear_bought")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")]
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
        InlineKeyboardButton(text="🧹 Очистить купленное", callback_data="clear_bought")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ К списку", callback_data="view_list")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
