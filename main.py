import asyncio
import logging
import sys
import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import start, shopping_list, ai_chat  # Заменили smart_ai на ai_chat
from utils.perplexity_client import perplexity_client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def clear_webhook(token: str):
    """Очистка webhook перед запуском polling"""
    try:
        url = f'https://api.telegram.org/bot{token}/deleteWebhook'
        response = requests.post(url)

        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                logger.info("✅ Webhook очищен для polling")
            else:
                logger.warning(f"⚠️ Ошибка очистки webhook: {result}")
        else:
            logger.warning(f"⚠️ HTTP ошибка при очистке webhook: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке webhook: {e}")


async def main():
    """Главная функция запуска бота"""

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден! Проверьте файл .env")
        return

    # Очищаем webhook перед запуском
    logger.info("🔧 Очищаем webhook для polling...")
    clear_webhook(BOT_TOKEN)

    # Создаем бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создаем диспетчер
    dp = Dispatcher()

    # ВАЖНО: Подключаем роутеры в правильном порядке
    # ai_chat должен быть ПОСЛЕДНИМ, так как он перехватывает все текстовые сообщения
    dp.include_router(start.router)
    dp.include_router(shopping_list.router)
    dp.include_router(ai_chat.router)  # В конце - перехватывает все сообщения

    logger.info("🔗 Роутеры подключены")

    try:
        # Инициализируем базу данных
        await init_db()
        logger.info("💾 База данных инициализирована")

        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_info.username}")
        logger.info(f"📋 ID бота: {bot_info.id}")

        # Устанавливаем команды бота
        await bot.set_my_commands([
            {"command": "start", "description": "🚀 Запустить бота"},
            {"command": "menu", "description": "📋 Главное меню"},
            {"command": "cancel", "description": "🚪 Выйти из AI-чата"},
        ])

        logger.info("🚀 Начинаем получение обновлений...")
        logger.info("🤖 AI-чат активен! Просто пишите вопросы в чат!")
        logger.info("📋 Команды: /menu или /cancel для выхода в главное меню")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
    finally:
        # Закрываем ресурсы
        await perplexity_client.close()
        await bot.session.close()
        logger.info("🛑 Бот остановлен")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}")
