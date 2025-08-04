from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from database import Database
from utils.perplexity_client import perplexity_client
from keyboards.inline import get_back_to_menu, get_main_menu
from config import PERPLEXITY_API_KEY

router = Router()
logger = logging.getLogger(__name__)


class AIAssistantState(StatesGroup):
    waiting_for_question = State()


@router.callback_query(F.data == "ai_help")
async def start_ai_assistant(callback: CallbackQuery, state: FSMContext):
    """Запуск AI помощника"""

    if not PERPLEXITY_API_KEY:
        await callback.message.edit_text(
            """
🤖 **AI Помощник недоступен**

Для работы AI помощника необходимо настроить ключ Perplexity API.

**Как получить ключ:**
1. Перейдите на https://www.perplexity.ai/settings/api
2. Создайте API ключ
3. Добавьте его в файл .env как `PERPLEXITY_API_KEY`

Пока что вы можете пользоваться обычными функциями бота.
            """,
            reply_markup=get_back_to_menu(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    await state.set_state(AIAssistantState.waiting_for_question)

    text = """
🤖 **AI Помощник активирован!**

Я могу помочь вам с любыми вопросами о продуктах и покупках.

**Примеры вопросов:**
• *"Что нужно для приготовления борща?"*
• *"Посоветуй здоровые продукты на неделю"*
• *"Что добавить к моему списку для завтраков?"*
• *"Идеи для быстрого ужина на двоих"*
• *"Какие продукты хорошо сочетаются с курицей?"*

**Напишите свой вопрос** или отправьте `/cancel` для выхода.

💡 *Я буду учитывать ваш текущий список покупок при ответе*
    """

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AIAssistantState.waiting_for_question)
async def handle_ai_question(message: Message, state: FSMContext):
    """Обработка вопроса к AI"""
    user_question = message.text.strip()
    user_id = message.from_user.id

    # Проверяем команду отмены
    if user_question.lower() in ['/cancel', 'отмена', 'cancel']:
        await state.clear()
        await message.answer(
            "🤖 AI помощник деактивирован",
            reply_markup=get_main_menu()
        )
        return

    # Проверяем длину вопроса
    if len(user_question) < 3:
        await message.answer(
            "❓ Пожалуйста, задайте более конкретный вопрос.",
            parse_mode="Markdown"
        )
        return

    # Показываем, что бот печатает
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Получаем текущий список покупок пользователя
    list_id = await Database.get_or_create_list(user_id)
    products = await Database.get_products(list_id) if list_id else []

    # Формируем список продуктов для AI
    current_list = []
    if products:
        current_list = [
            f"{p['name']} ({p['quantity']})" + (" - куплено" if p['is_bought'] else "")
            for p in products
        ]

    logger.info(f"🤖 Пользователь {user_id} задал вопрос AI: {user_question[:50]}...")

    # Получаем ответ от AI
    ai_response = await perplexity_client.get_shopping_suggestions(
        user_question,
        current_list
    )

    # Формируем ответ
    response_header = "🤖 **AI Помощник отвечает:**\n\n"

    # Ограничиваем длину ответа (Telegram лимит ~4096 символов)
    if len(ai_response) > 3500:
        ai_response = ai_response[:3500] + "...\n\n*[Ответ сокращен из-за ограничений Telegram]*"

    full_response = response_header + ai_response

    await message.answer(
        text=full_response,
        reply_markup=get_back_to_menu(),
        parse_mode="Markdown"
    )

    logger.info(f"✅ AI ответ отправлен пользователю {user_id}")
    await state.clear()


# Дополнительный обработчик для быстрых AI команд
@router.message(F.text.startswith("AI:") | F.text.startswith("ai:") | F.text.startswith("АИ:"))
async def quick_ai_question(message: Message):
    """Быстрый вопрос к AI без входа в режим диалога"""

    if not PERPLEXITY_API_KEY:
        await message.answer(
            "🤖 AI помощник недоступен. Настройте ключ Perplexity API.",
            reply_markup=get_main_menu()
        )
        return

    # Извлекаем вопрос после префикса
    question = message.text[3:].strip()  # Убираем "AI:" и пробелы

    if len(question) < 3:
        await message.answer(
            "❓ Напишите вопрос после 'AI:'\n\nПример: `AI: Что нужно для салата Цезарь?`",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        return

    await message.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    list_id = await Database.get_or_create_list(user_id)
    products = await Database.get_products(list_id) if list_id else []

    current_list = [f"{p['name']} ({p['quantity']})" for p in products if not p['is_bought']]

    ai_response = await perplexity_client.get_shopping_suggestions(question, current_list)

    response_text = f"🤖 **AI:** {ai_response}"

    if len(response_text) > 4000:
        response_text = response_text[:4000] + "..."

    await message.answer(
        text=response_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

    logger.info(f"✅ Быстрый AI ответ отправлен пользователю {user_id}")
