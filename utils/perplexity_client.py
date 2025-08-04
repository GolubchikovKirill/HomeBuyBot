import aiohttp
import asyncio
import ssl
import certifi
from typing import List, Optional
from config import PERPLEXITY_API_KEY, PERPLEXITY_API_URL
import logging

logger = logging.getLogger(__name__)


class PerplexityClient:
    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.api_url = PERPLEXITY_API_URL
        self.session = None

    async def get_session(self):
        """Получить aiohttp сессию"""
        if self.session is None or self.session.closed:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self.session

    async def close(self):
        """Закрыть сессию"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_shopping_suggestions(self, user_message: str, current_list: List[str] = None) -> str:
        """Получить рекомендации по списку покупок от AI"""

        if not self.api_key:
            return "🤖 AI помощник недоступен. Настройте PERPLEXITY_API_KEY в .env файле."

        # Формируем контекст
        if current_list and len(current_list) > 0:
            list_text = "Текущий список покупок: " + ", ".join(current_list[:5])
        else:
            list_text = "Список покупок пуст"

        # НОВЫЕ актуальные модели Perplexity 2025 (с Pro подпиской)
        models_to_try = [
            "sonar-pro",  # Основная модель для сложных запросов
            "sonar",  # Быстрая модель для простых запросов
            "sonar-reasoning",  # Модель с цепочкой рассуждений
            "sonar-deep-research",  # Глубокие исследования
            "r1-1776"  # Офлайн модель (без поиска)
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        session = await self.get_session()

        for model in models_to_try:
            try:
                # Формируем payload для новых моделей Sonar
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты помощник для составления списка покупок. Отвечай на русском языке кратко и полезно. Используй эмодзи для наглядности."
                        },
                        {
                            "role": "user",
                            "content": f"{list_text}. Вопрос пользователя: {user_message}"
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3,
                    "stream": False
                }

                # Для моделей с поиском добавляем web_search_options
                if model in ["sonar", "sonar-pro", "sonar-reasoning", "sonar-deep-research"]:
                    payload["web_search_options"] = {
                        "search_context_size": "medium",
                        "top_k": 3,
                        "return_related_questions": False,
                        "search_recency_filter": "month"  # Последний месяц
                    }

                logger.info(f"🔗 Пробуем новую модель 2025: {model}")

                async with session.post(
                        self.api_url,
                        json=payload,
                        headers=headers
                ) as response:

                    logger.info(f"📡 Perplexity ответ для {model}: статус {response.status}")

                    if response.status == 200:
                        result = await response.json()
                        ai_response = result['choices'][0]['message']['content']
                        logger.info(f"✅ Успешный ответ от модели 2025: {model}")
                        return f"🤖 {ai_response}"

                    elif response.status == 401:
                        logger.error("❌ Неверный API ключ Perplexity")
                        return "🤖 Неверный API ключ. Получите новый ключ на https://www.perplexity.ai/settings/api"

                    elif response.status == 429:
                        logger.error("❌ Превышен лимит запросов")
                        return "🤖 Слишком много запросов. Попробуйте через минуту."

                    elif response.status == 400:
                        response_text = await response.text()
                        logger.error(f"❌ Ошибка 400 с моделью {model}: {response_text[:200]}")
                        continue

                    elif response.status == 403:
                        logger.error(f"❌ Модель {model} недоступна для вашего плана")
                        continue

                    else:
                        response_text = await response.text()
                        logger.error(f"❌ Ошибка {response.status} с моделью {model}: {response_text[:200]}")
                        continue

            except asyncio.TimeoutError:
                logger.error(f"⏰ Таймаут для модели {model}")
                continue

            except Exception as e:
                logger.error(f"❌ Ошибка с моделью {model}: {type(e).__name__}: {e}")
                continue

        # Если ни одна модель не работает
        logger.error("❌ Все новые модели Perplexity 2025 недоступны")
        return """🤖 AI помощник временно недоступен.

**Возможные причины:**
• Проблема с API ключом Perplexity
• Превышен лимит Pro подписки
• Технические проблемы Perplexity

**Решение:**
1. Проверьте ключ на https://www.perplexity.ai/settings/api
2. Убедитесь, что Pro подписка активна
3. Попробуйте позже"""


# Глобальный экземпляр клиента
perplexity_client = PerplexityClient()
