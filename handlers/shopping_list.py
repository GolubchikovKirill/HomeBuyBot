from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import datetime

from database import Database
from keyboards.inline import get_main_menu, get_list_actions, get_back_to_menu, get_product_management_keyboard

router = Router()
logger = logging.getLogger(__name__)


class AddProductState(StatesGroup):
    waiting_for_product = State()


@router.callback_query(F.data == "view_list")
async def view_shopping_list(callback: CallbackQuery):
    """Показать список покупок"""
    try:
        user_id = callback.from_user.id
        list_id = await Database.get_or_create_list(user_id)

        if not list_id:
            await callback.message.edit_text(
                "❌ Ошибка при загрузке списка покупок.",
                reply_markup=get_back_to_menu()
            )
            return

        products = await Database.get_products(list_id)
        logger.info(f"📋 Загружено {len(products)} продуктов для пользователя {user_id}")

        # Добавляем временную метку для избежания дублирования
        timestamp = datetime.datetime.now().strftime("%H:%M")

        if not products:
            text = f"""
📝 **Ваш список покупок пуст** _(обн. {timestamp})_

Добавьте первые продукты, чтобы начать планирование покупок!

💡 *Совет: Нажмите "Добавить продукт" ниже*
            """
        else:
            text = f"🛒 **Ваш список покупок** _(обн. {timestamp})_\n\n"

            unbought_count = 0
            bought_count = 0

            for product in products:
                if product['is_bought']:
                    status = "✅"
                    name_display = f"~~{product['name']}~~"
                    bought_count += 1
                else:
                    status = "🔘"
                    name_display = f"**{product['name']}**"
                    unbought_count += 1

                quantity_display = f" _{product['quantity']}_" if product['quantity'] != '1' else ""
                text += f"{status} {name_display}{quantity_display}\n"

            text += f"\n📊 **Итого:** {len(products)} товаров"
            text += f"\n🔘 К покупке: {unbought_count}"
            text += f"\n✅ Куплено: {bought_count}"

        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=get_list_actions(),
                parse_mode="Markdown"
            )
        except Exception as edit_error:
            # Если не можем отредактировать, отправляем новое сообщение
            await callback.message.delete()
            await callback.message.answer(
                text=text,
                reply_markup=get_list_actions(),
                parse_mode="Markdown"
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при просмотре списка: {e}")
        await callback.answer("❌ Ошибка при загрузке списка", show_alert=True)


@router.callback_query(F.data == "manage_products")
async def manage_products(callback: CallbackQuery):
    """Управление продуктами - удаление и изменение статуса"""
    try:
        user_id = callback.from_user.id
        list_id = await Database.get_or_create_list(user_id)
        products = await Database.get_products(list_id)

        if not products:
            await callback.message.edit_text(
                "📝 **Список пуст**\n\nДобавьте продукты для управления ими.",
                reply_markup=get_list_actions(),
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        text = "🗑 **Управление товарами**\n\n"
        text += "• Нажмите на товар, чтобы отметить купленным/не купленным\n"
        text += "• Нажмите 🗑 для удаления товара\n\n"
        text += f"**Всего товаров:** {len(products)}"

        await callback.message.edit_text(
            text=text,
            reply_markup=get_product_management_keyboard(products),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при управлении продуктами: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    """Начать добавление продукта"""
    try:
        await state.set_state(AddProductState.waiting_for_product)

        text = """
➕ **Добавление продукта**

Напишите название продукта и количество:

**Примеры:**
• `Молоко`
• `Хлеб 2 буханки`  
• `Яблоки 1 кг`
• `Помидоры 500г`

Или отправьте `/cancel` для отмены
        """

        await callback.message.edit_text(text=text, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске добавления продукта: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(AddProductState.waiting_for_product)
async def add_product_handler(message: Message, state: FSMContext):
    """Обработка добавления продукта"""
    try:
        # Проверяем команду отмены
        if message.text and message.text.lower() in ['/cancel', 'отмена', 'cancel']:
            await state.clear()
            await message.answer(
                "❌ Добавление отменено.",
                reply_markup=get_main_menu()
            )
            return

        product_text = message.text.strip()

        if not product_text:
            await message.answer("❌ Название продукта не может быть пустым!")
            return

        # Улучшенное разделение названия и количества
        words = product_text.split()
        product_name = product_text
        quantity = '1'

        if len(words) > 1:
            last_word = words[-1].lower()
            units = ['кг', 'г', 'гр', 'л', 'мл', 'шт', 'штук', 'упак', 'пачка', 'банка', 'бутылка']

            # Проверяем есть ли единица измерения
            if any(unit in last_word for unit in units):
                if len(words) >= 2 and words[-2].replace(',', '.').replace('.', '').isdigit():
                    quantity = f"{words[-2]} {words[-1]}"
                    product_name = ' '.join(words[:-2])
                else:
                    quantity = words[-1]
                    product_name = ' '.join(words[:-1])
            # Проверяем последнее слово на число
            elif last_word.replace(',', '.').replace('.', '').isdigit():
                quantity = words[-1]
                product_name = ' '.join(words[:-1])

        if not product_name.strip():
            product_name = product_text
            quantity = '1'

        # Добавляем в базу данных
        user_id = message.from_user.id
        list_id = await Database.get_or_create_list(user_id)

        if list_id:
            await Database.add_product(list_id, product_name, quantity)

            success_text = f"✅ **Продукт добавлен!**\n\n📦 **{product_name}**"
            if quantity != '1':
                success_text += f" _{quantity}_"

            logger.info(f"➕ Продукт добавлен: {product_name} ({quantity}) для пользователя {user_id}")

            await message.answer(
                text=success_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "❌ Ошибка при добавлении продукта. Попробуйте еще раз.",
                reply_markup=get_main_menu()
            )

        await state.clear()

    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении продукта: {e}")
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при добавлении продукта.",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data.startswith("toggle_"))
async def toggle_product_status(callback: CallbackQuery):
    """Изменить статус продукта (куплен/не куплен)"""
    try:
        product_id = int(callback.data.split("_")[1])
        success = await Database.toggle_product_bought(product_id)

        if success:
            await callback.answer("✅ Статус изменен!", show_alert=False)
            # Обновляем страницу управления
            await manage_products(callback)
        else:
            await callback.answer("❌ Ошибка при изменении статуса", show_alert=True)

    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка в данных", show_alert=True)
    except Exception as e:
        logger.error(f"❌ Ошибка toggle: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("delete_"))
async def delete_product_handler(callback: CallbackQuery):
    """Удалить продукт из списка"""
    try:
        product_id = int(callback.data.split("_")[1])
        success = await Database.delete_product(product_id)

        if success:
            await callback.answer("🗑 Продукт удален!", show_alert=False)
            # Обновляем страницу управления
            await manage_products(callback)
        else:
            await callback.answer("❌ Ошибка при удалении", show_alert=True)

    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка в данных", show_alert=True)
    except Exception as e:
        logger.error(f"❌ Ошибка delete: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "clear_bought")
async def clear_bought_products(callback: CallbackQuery):
    """Очистить купленные продукты"""
    try:
        user_id = callback.from_user.id
        list_id = await Database.get_or_create_list(user_id)

        if list_id:
            deleted_count = await Database.clear_bought_products(list_id)

            if deleted_count > 0:
                await callback.answer(f"🧹 Удалено {deleted_count} купленных товаров", show_alert=True)
                logger.info(f"🧹 Пользователь {user_id} очистил {deleted_count} товаров")

                # Определяем, с какой страницы вызвана функция
                if "manage_products" in str(callback.message.reply_markup):
                    await manage_products(callback)
                else:
                    await view_shopping_list(callback)
            else:
                await callback.answer("ℹ️ Нет купленных товаров для удаления", show_alert=True)
        else:
            await callback.answer("❌ Ошибка при очистке списка", show_alert=True)

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке: {e}")
        await callback.answer("❌ Ошибка при очистке", show_alert=True)
