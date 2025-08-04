#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv()


def fix_telegram_webhook():
    """Удаляем активный webhook для polling"""
    bot_token = os.getenv('BOT_TOKEN')

    if not bot_token:
        print("❌ BOT_TOKEN не найден в .env файле")
        return False

    print(f"🔧 Проверяем webhook для бота...")

    # Проверяем информацию о webhook
    webhook_info_url = f'https://api.telegram.org/bot{bot_token}/getWebhookInfo'
    try:
        response = requests.get(webhook_info_url)
        if response.status_code == 200:
            info = response.json()
            if info['ok']:
                webhook_url = info['result'].get('url', '')
                if webhook_url:
                    print(f"⚠️ Активен webhook: {webhook_url}")
                else:
                    print("ℹ️ Webhook не активен")
            else:
                print(f"❌ Ошибка получения info: {info}")
                return False
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

    # Удаляем webhook
    delete_url = f'https://api.telegram.org/bot{bot_token}/deleteWebhook'
    try:
        response = requests.post(delete_url)
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ Webhook успешно удален!")
                return True
            else:
                print(f"❌ Ошибка удаления: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка при удалении: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Исправление Telegram webhook конфликта\n")

    if fix_telegram_webhook():
        print("\n✅ Готово! Теперь можно запустить бота:")
        print("uv run main.py")
    else:
        print("\n❌ Не удалось исправить webhook")
        print("Попробуйте вручную через curl или BotFather")
