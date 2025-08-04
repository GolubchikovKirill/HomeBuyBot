import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import start, shopping_list, ai_assistant, common
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


async def main():
    """Главная функция запуска бота"""

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден! Проверьте файл .env")
        return

    # Создаем бота с настройками по умолчанию
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создаем диспетчер
    dp = Dispatcher()

    # Подключаем роутеры в правильном порядке (от специфичных к общим)
    dp.include_router(start.router)
    dp.include_router(shopping_list.router)
    dp.include_router(ai_assistant.router)
    dp.include_router(common.router)  # Общие обработчики в конце

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
        ])

        # Запускаем polling
        logger.info("🚀 Начинаем получение обновлений...")
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
