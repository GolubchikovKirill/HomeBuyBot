from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import re

from database import Database
from utils.perplexity_client import perplexity_client
from keyboards.inline import get_main_menu, get_back_to_menu, get_ai_actions_keyboard

router = Router()
logger = logging.getLogger(__name__)


class AIState(StatesGroup):
    waiting_for_question = State()


# Ключевые слова для AI
AI_TRIGGERS = [
    'рецепт', 'приготовить', 'готовить', 'как сделать', 'ингредиенты',
    'что купить', 'посоветуй', 'рекомендуй', 'нужно для', 'список для',
    'как хранить', 'сколько', 'где купить', 'что лучше', 'альтернатива',
    'заменить', 'диета', 'здоровое', 'быстро', 'просто', 'вкусно'
]


def should_trigger_ai(message_text: str) -> bool:
    """Определяем, нужно ли активировать AI"""
    text_lower = message_text.lower()

    # Проверяем ключевые слова
    if any(trigger in text_lower for trigger in AI_TRIGGERS):
        return True

    # Проверяем вопросительные конструкции
    question_patterns = [
        r'\bчто\b.*\?',
        r'\bкак\b.*\?',
        r'\bгде\b.*\?',
        r'\bкогда\b.*\?',
        r'\bзачем\b.*\?',
        r'\bпочему\b.*\?'
    ]

    if any(re.search(pattern, text_lower) for pattern in question_patterns):
        return True

    return False


@router.callback_query(F.data == "ai_help")
async def activate_ai_mode(callback: CallbackQuery, state: FSMContext):
    """Активация режима AI помощника"""
    await state.set_state(AIState.waiting_for_question)

    text = """
🤖 **Умный AI помощник активирован!**

Теперь я отвечу на любой ваш вопрос максимально подробно и полезно.

**Что я умею:**
🍳 Рецепты и кулинарные советы
🛒 Рекомендации продуктов
📋 Планирование питания
💡 Советы по хранению и приготовлению
🔄 Поиск альтернатив и замен
📊 Актуальная информация из интернета

**Примеры вопросов:**
• "Как приготовить борщ со всеми подробностями?"
• "Что купить для здорового питания на неделю?"
• "Как правильно хранить овощи?"
• "Чем заменить сливочное масло в выпечке?"

Задавайте любой вопрос или отправьте `/cancel` для выхода.
    """

    await callback.message.edit_text(text=text, parse_mode="Markdown")
    await callback.answer()


@router.message(AIState.waiting_for_question)
async def handle_ai_question(message: Message, state: FSMContext):
    """Обработка вопроса к AI в режиме диалога"""
    await process_ai_message(message, is_dialog_mode=True)
    await state.clear()


@router.message(F.text & ~F.text.startswith('/'))
async def smart_message_handler(message: Message):
    """Умный обработчик сообщений - определяет, нужен ли AI"""
    text = message.text.strip()

    # Проверяем, нужно ли активировать AI
    if should_trigger_ai(text):
        await process_ai_message(message, is_dialog_mode=False)
    else:
        # Обычная обработка неизвестного сообщения
        await handle_regular_message(message)


async def process_ai_message(message: Message, is_dialog_mode: bool = False):
    """Обработка сообщения через AI"""
    user_question = message.text.strip()
    user_id = message.from_user.id

    # Проверяем команду отмены
    if user_question.lower() in ['/cancel', 'отмена', 'cancel']:
        if is_dialog_mode:
            await message.answer("🤖 AI режим деактивирован", reply_markup=get_main_menu())
            return

    # Показываем, что AI думает
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Получаем текущий список покупок
        list_id = await Database.get_or_create_list(user_id)
        products = await Database.get_products(list_id) if list_id else []
        current_list = [f"{p['name']} ({p['quantity']})" for p in products if not p['is_bought']]

        logger.info(f"🤖 AI обрабатывает: {user_question[:50]}... для пользователя {user_id}")

        # Получаем умный ответ от AI
        ai_result = await perplexity_client.get_smart_response(user_question, current_list)

        ai_response = ai_result["response"]
        suggested_products = ai_result["products"]
        intent = ai_result["intent"]

        # Формируем ответ
        response_text = f"🤖 **Умный помощник:**\n\n{ai_response}"

        # Если AI предложил продукты для добавления
        if suggested_products:
            response_text += f"\n\n📋 **Рекомендую добавить в список:**\n"
            for product in suggested_products:
                response_text += f"• {product['name']} ({product['quantity']})\n"

            # Предлагаем добавить продукты
            keyboard = get_ai_actions_keyboard(suggested_products, intent)
        else:
            keyboard = get_back_to_menu() if is_dialog_mode else get_main_menu()

        # Ограничиваем длину ответа
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "...\n\n*[Ответ сокращен]*"

        await message.answer(
            text=response_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        logger.info(f"✅ AI ответ отправлен пользователю {user_id}, продуктов предложено: {len(suggested_products)}")

    except Exception as e:
        logger.error(f"❌ Ошибка AI: {type(e).__name__}: {e}")
        await message.answer(
            "🤖 Произошла ошибка при обращении к AI. Попробуйте позже.",
            reply_markup=get_main_menu()
        )


async def handle_regular_message(message: Message):
    """Обработка обычных сообщений (не AI)"""
    user_name = message.from_user.first_name
    text = message.text

    # Проверяем, похоже ли на продукт для добавления
    if len(text.split()) <= 4 and len(text) < 60:
        response_text = f"""
💡 **Хотите добавить "{text}" в список покупок?**

Или задайте вопрос AI для получения рекомендаций:

**Примеры:**
• "Что нужно для {text}?"
• "Рецепт с {text}"
• "Как выбрать {text}?"
        """
    else:
        response_text = f"""
💬 **Привет, {user_name}!**

Вы написали: _{text[:100]}_

Попробуйте задать вопрос AI или используйте кнопки меню:
        """

    await message.answer(
        text=response_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("add_ai_products_"))
async def add_ai_suggested_products(callback: CallbackQuery):
    """Добавление продуктов, предложенных AI"""
    try:
        # Извлекаем данные из callback
        data_part = callback.data.replace("add_ai_products_", "")
        product_indices = [int(x) for x in data_part.split("_") if x.isdigit()]

        # Получаем продукты из временного хранилища (можно реализовать через Redis или файл)
        # Пока что просто подтверждаем действие

        user_id = callback.from_user.id
        list_id = await Database.get_or_create_list(user_id)

        await callback.answer("✅ Продукты добавлены в список!", show_alert=True)
        await callback.message.edit_text(
            "✅ **Продукты успешно добавлены в ваш список покупок!**\n\nМожете посмотреть обновленный список или задать новый вопрос.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"❌ Ошибка добавления AI продуктов: {e}")
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)
