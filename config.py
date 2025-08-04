import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токены и API ключи
BOT_TOKEN = os.getenv('BOT_TOKEN')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Настройки базы данных
DATABASE_URL = 'shopping.db'

# ID администраторов (замените на свой Telegram ID)
ADMIN_IDS = [164406794]  # Получить свой ID: @userinfobot

# Настройки Perplexity API
PERPLEXITY_API_URL = 'https://api.perplexity.ai/chat/completions'

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")

if not PERPLEXITY_API_KEY:
    print("⚠️ PERPLEXITY_API_KEY не найден - AI функции будут недоступны")
