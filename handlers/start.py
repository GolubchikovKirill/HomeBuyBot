from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
import logging

from database import Database
from keyboards.inline import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_command(message: Message):
    """Обработчик команды /start"""
    user = message.from_user

    # Регистрируем пользователя в базе данных
    await Database.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    logger.info(f"👋 Пользователь {user.id} ({user.first_name}) запустил бота")

    welcome_text = f"""
🛒 **Привет, {user.first_name}!**

Я твой умный помощник для ведения семейного списка покупок!

**Что я умею:**
✅ Вести списки продуктов для всей семьи
✅ Отмечать купленные товары одним нажатием
✅ Давать умные рекомендации с помощью AI
✅ Предлагать рецепты и дополнительные продукты
✅ Помочь не забыть ничего важного

Давайте начнем! 🚀
    """

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user = callback.from_user

    menu_text = f"""
🏠 **Главное меню**

Привет, {user.first_name}! Что будем делать?
    """

    await callback.message.edit_text(
        text=menu_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

    await callback.answer()
