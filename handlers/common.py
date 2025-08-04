from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import logging

from database import Database
from keyboards.inline import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text & ~F.text.startswith('/') & ~F.text.startswith('AI:'))
async def handle_unknown_text(message: Message):
    """Обработка неизвестных текстовых сообщений"""
    user_name = message.from_user.first_name
    text = message.text.strip()

    logger.info(f"📩 Пользователь {message.from_user.id} отправил: {text[:50]}")

    # Проверяем, похоже ли это на продукт
    if len(text.split()) <= 4 and len(text) < 60 and not any(
            char in text for char in ['?', '!', 'как', 'что', 'где', 'когда']):
        # Предлагаем добавить как продукт
        response_text = f"""
💡 **Хотите добавить "{text}" в список покупок?**

**Способы добавления:**
• Нажмите "➕ Добавить продукт" ниже
• Напишите `AI: добавь {text}` для умного добавления

**Или используйте другие функции:**
        """
    else:
        response_text = f"""
💬 **Привет, {user_name}!**

Вы написали: _{text[:100]}_

Для управления ботом используйте кнопки меню ниже 👇

**Быстрые команды:**
• `/start` - перезапустить бота
• `AI: ваш вопрос` - быстрый вопрос к AI
        """

    await message.answer(
        text=response_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Обработка неизвестных callback запросов"""
    logger.warning(f"❓ Неизвестный callback: {callback.data}")

    await callback.answer(
        "❓ Неизвестная команда. Используйте кнопки меню.",
        show_alert=True
    )
