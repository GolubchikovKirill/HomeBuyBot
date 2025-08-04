from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from database import Database
from utils.perplexity_client import perplexity_client
from keyboards.inline import get_main_menu, get_ai_chat_keyboard

router = Router()
logger = logging.getLogger(__name__)


class AIChatState(StatesGroup):
    chatting = State()


@router.message(F.text & ~F.text.startswith('/') & ~F.text.startswith('AI:'))
async def ai_chat_handler(message: Message, state: FSMContext):
    """Основной обработчик AI чата - активируется автоматически при любом сообщении"""

    user_id = message.from_user.id
    user_message = message.text.strip()
    user_name = message.from_user.first_name

    # Активируем состояние AI чата
    await state.set_state(AIChatState.chatting)

    # Проверяем, не первое ли это сообщение в сессии
    current_state = await state.get_state()
    if current_state != AIChatState.chatting.state:
        # Отправляем приветственное сообщение
        welcome_text = f"""
🤖 **Привет, {user_name}!** 

Я перешел в режим AI-чата. Теперь просто пишите мне вопросы, и я буду отвечать!

💡 **Для выхода в меню используйте:**
• Команду `/menu` или `/cancel`
• Кнопку "📋 Главное меню" под моими ответами

---

**Ваш вопрос:** {user_message}
        """

        # Отправляем приветствие
        await message.answer(
            text=welcome_text,
            parse_mode="Markdown"
        )

    # Показываем, что AI думает
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Получаем текущий список покупок пользователя
        list_id = await Database.get_or_create_list(user_id)
        products = await Database.get_products(list_id) if list_id else []
        current_list = [f"{p['name']} ({p['quantity']})" for p in products if not p['is_bought']]

        logger.info(f"🤖 AI чат - пользователь {user_id}: {user_message[:50]}...")

        # Получаем умный ответ от AI
        ai_result = await perplexity_client.get_smart_response(user_message, current_list)

        ai_response = ai_result["response"]
        suggested_products = ai_result["products"]
        intent = ai_result["intent"]
        model = ai_result.get("model", "unknown")

        # Формируем ответ
        response_text = f"🤖 **AI помощник** _(модель: {model})_\n\n{ai_response}"

        # Если AI предложил продукты для добавления
        if suggested_products:
            response_text += f"\n\n📋 **💡 Рекомендую добавить в список:**\n"
            for product in suggested_products:
                response_text += f"• {product['name']} ({product['quantity']})\n"

        # Ограничиваем длину ответа
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "...\n\n*[Ответ сокращен]*"

        # Добавляем подсказку для продолжения
        response_text += f"\n\n💬 *Продолжайте задавать вопросы или используйте кнопки ниже*"

        # Отправляем ответ с клавиатурой
        await message.answer(
            text=response_text,
            reply_markup=get_ai_chat_keyboard(suggested_products, intent),
            parse_mode="Markdown"
        )

        logger.info(f"✅ AI чат ответ отправлен пользователю {user_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка AI чата: {type(e).__name__}: {e}")
        await message.answer(
            "🤖 Произошла ошибка при обращении к AI. Попробуйте еще раз или перейдите в меню.",
            reply_markup=get_ai_chat_keyboard([], "error")
        )


@router.message(F.text.in_(['/menu', '/cancel', 'меню', 'отмена']))
async def exit_ai_chat(message: Message, state: FSMContext):
    """Выход из AI чата в главное меню"""
    await state.clear()

    await message.answer(
        "📋 **Вы вышли из AI-чата**\n\nВернулись в главное меню. Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

    logger.info(f"🚪 Пользователь {message.from_user.id} вышел из AI чата")


@router.callback_query(F.data == "exit_ai_chat")
async def exit_ai_chat_button(callback: CallbackQuery, state: FSMContext):
    """Выход из AI чата через кнопку"""
    await state.clear()

    await callback.message.edit_text(
        "📋 **Вы вышли из AI-чата**\n\nВернулись в главное меню. Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

    await callback.answer("Вышли из AI-чата")
    logger.info(f"🚪 Пользователь {callback.from_user.id} вышел из AI чата через кнопку")


@router.callback_query(F.data == "ai_help")
async def activate_ai_chat(callback: CallbackQuery, state: FSMContext):
    """Активация AI чата через кнопку"""
    await state.set_state(AIChatState.chatting)

    text = f"""
🤖 **AI-чат активирован!**

Привет, {callback.from_user.first_name}! Пишите мне вопросы в чат, и я буду отвечать.

**Что я умею:**
🍳 Рецепты и кулинарные советы с актуальной информацией
🛒 Умные рекомендации продуктов
📋 Планирование питания и меню
💡 Советы по хранению и приготовлению
🔄 Поиск альтернатив и замен
📊 Актуальная информация из интернета

**Примеры вопросов:**
• "Как приготовить итальянскую пасту?"
• "Что купить для здорового завтрака?"
• "Чем заменить молоко в выпечке?"
• "Какие продукты сейчас в сезон?"

💬 **Напишите свой вопрос!**
    """

    await callback.message.edit_text(
        text=text,
        reply_markup=get_ai_chat_keyboard([], "welcome"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_ai_products_"))
async def add_ai_suggested_products(callback: CallbackQuery, state: FSMContext):
    """Добавление продуктов, предложенных AI"""
    try:
        # В реальной реализации здесь нужно сохранить предложенные продукты в state
        # Пока что просто подтверждаем действие

        await callback.answer("✅ Функция добавления продуктов от AI скоро будет доступна!", show_alert=True)

    except Exception as e:
        logger.error(f"❌ Ошибка добавления AI продуктов: {e}")
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)
