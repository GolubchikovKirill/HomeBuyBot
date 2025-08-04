import aiohttp
import asyncio
import ssl
import certifi
import re
from typing import List, Optional, Dict
from config import PERPLEXITY_API_KEY, PERPLEXITY_API_URL
import logging

logger = logging.getLogger(__name__)


class PerplexityClient:
    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.api_url = "https://api.perplexity.ai/chat/completions"
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

    def extract_products_from_response(self, ai_response: str) -> List[Dict[str, str]]:
        """Извлекаем продукты из ответа AI для автоматического добавления"""
        products = []

        # Ищем списки продуктов в ответе
        patterns = [
            r'[\-\*\•]\s*([А-Яа-я\s]+(?:\d+\s*(?:кг|г|л|мл|шт|штук|упак|пачка|банка|буханка)?))',
            r'\d+\.\s*([А-Яа-я\s]+(?:\d+\s*(?:кг|г|л|мл|шт|штук|упак|пачка|банка|буханка)?))',
            r'([А-Яа-я]+)\s*-\s*(\d+\s*(?:кг|г|л|мл|шт|штук|упак|пачка|банка))',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, ai_response, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    name, quantity = match
                    products.append({"name": name.strip(), "quantity": quantity.strip()})
                else:
                    parts = match.strip().split()
                    if len(parts) > 1 and any(
                            unit in parts[-1].lower() for unit in ['кг', 'г', 'л', 'мл', 'шт', 'упак']):
                        name = ' '.join(parts[:-1])
                        quantity = parts[-1]
                    else:
                        name = match.strip()
                        quantity = '1'

                    if name and len(name) > 2:
                        products.append({"name": name, "quantity": quantity})

        # Убираем дубликаты
        unique_products = []
        seen = set()
        for product in products:
            key = product['name'].lower()
            if key not in seen and len(key) > 2:
                seen.add(key)
                unique_products.append(product)

        return unique_products[:5]

    async def get_smart_response(self, user_message: str, current_list: List[str] = None,
                                 context: str = "general") -> Dict:
        """Получить умный ответ от AI с анализом намерений"""

        if not self.api_key:
            return {
                "response": "🤖 AI помощник недоступен. Настройте PERPLEXITY_API_KEY в .env файле.",
                "products": [],
                "intent": "error"
            }

        # Формируем контекст
        if current_list and len(current_list) > 0:
            list_context = f"Текущий список покупок: {', '.join(current_list[:8])}"
        else:
            list_context = "Список покупок пуст"

        # Улучшенный системный промпт
        system_prompt = f"""Ты - умный семейный помощник для списка покупок. 

КОНТЕКСТ: {list_context}

ТВОИ ЗАДАЧИ:
1. Отвечать на вопросы о продуктах, рецептах, приготовлении еды
2. Рекомендовать продукты для покупки
3. Помогать с планированием питания
4. Давать советы по хранению продуктов
5. Предлагать альтернативы и замены продуктов

ФОРМАТ ОТВЕТОВ:
- Отвечай подробно и полезно (300-500 слов)
- Используй эмодзи для наглядности
- Структурируй ответ: заголовки, списки, советы
- Если рекомендуешь продукты, выделяй их списком с маркерами
- Давай практические советы и лайфхаки

ЯЗЫК: Только русский язык

СТИЛЬ: Дружелюбный, экспертный, практичный"""

        # ИСПРАВЛЕНО: Возвращаем рабочие модели
        models_to_try = [
            "sonar-pro",  # Работала ранее
            "sonar",  # Быстрая модель
            "sonar-reasoning",  # Модель с рассуждениями
            "sonar-deep-research"  # Глубокие исследования
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        session = await self.get_session()

        for model in models_to_try:
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": 800,
                    "temperature": 0.4,
                    "stream": False
                }

                # Добавляем web_search_options для online моделей
                if model in ["sonar", "sonar-pro", "sonar-reasoning", "sonar-deep-research"]:
                    payload["web_search_options"] = {
                        "search_context_size": "medium",
                        "top_k": 3,
                        "return_related_questions": False,
                        "search_recency_filter": "month"
                    }

                logger.info(f"🔗 Запрос к умному AI: {model}")

                async with session.post(
                        self.api_url,
                        json=payload,
                        headers=headers
                ) as response:

                    if response.status == 200:
                        result = await response.json()
                        ai_response = result['choices'][0]['message']['content']

                        # Извлекаем продукты из ответа
                        products = self.extract_products_from_response(ai_response)

                        # Определяем намерение пользователя
                        intent = self.detect_intent(user_message, ai_response)

                        logger.info(f"✅ Умный ответ от {model}, найдено продуктов: {len(products)}")

                        return {
                            "response": ai_response,
                            "products": products,
                            "intent": intent,
                            "model": model
                        }
                    else:
                        response_text = await response.text()
                        logger.warning(f"❌ Ошибка {response.status} с моделью {model}: {response_text[:100]}")
                        continue

            except Exception as e:
                logger.error(f"❌ Ошибка с моделью {model}: {e}")
                continue

        # ИСПРАВЛЕНО: Fallback на простые ответы
        return await self.get_simple_ai_response(user_message, current_list)

    async def get_simple_ai_response(self, user_message: str, current_list: List[str] = None) -> Dict:
        """Простой AI без API - fallback решение"""

        simple_responses = {
            "привет": "🤖 **Привет!** Я ваш семейный помощник для списка покупок. Задавайте вопросы о продуктах, рецептах или планировании питания!",
            "123": "🤖 **Получил ваше сообщение!** Попробуйте задать вопрос о еде, рецептах или продуктах. Например: 'Что нужно для борща?' или 'Продукты для завтрака'",
            "борщ": "🍲 **Для борща понадобится:**\n\n• Свекла - 2-3 штуки\n• Капуста - 200г\n• Морковь - 1 штука\n• Лук - 1 штука\n• Картофель - 3-4 штуки\n• Мясо говядина - 500г\n• Томатная паста - 2 ст.л.\n• Зелень (укроп, петрушка)\n• Сметана для подачи\n\n**Совет:** Свеклу лучше отварить заранее!",
            "завтрак": "🥐 **Для полноценного завтрака:**\n\n• Яйца - 6 штук\n• Хлеб - 1 буханка\n• Молоко - 1 литр\n• Масло сливочное - 200г\n• Сыр - 300г\n• Колбаса - 200г\n• Кофе\n• Чай\n• Овсянка - 500г\n• Фрукты (бананы, яблоки)",
            "ужин": "🍽 **Для ужина рекомендую:**\n\n• Мясо или рыба - 600г\n• Гарнир: рис/макароны/картофель\n• Свежие овощи для салата\n• Зелень\n• Специи и приправы\n\n**Идеи:** Курица с рисом, рыба с овощами, говядина с картофелем",
            "салат": "🥗 **Для свежего салата:**\n\n• Огурцы - 3 штуки\n• Помидоры - 4 штуки\n• Листья салата\n• Лук красный - 1 штука\n• Морковь - 1 штука\n• Растительное масло\n• Соль, перец\n• Лимон для заправки",
            "выпечка": "🧁 **Для выпечки базовый набор:**\n\n• Мука - 1кг\n• Яйца - 10 штук\n• Сахар - 500г\n• Масло сливочное - 500г\n• Молоко - 1 литр\n• Разрыхлитель\n• Ванилин\n• Соль\n\n**Совет:** Все ингредиенты должны быть комнатной температуры!",
            "здоровое": "🥗 **Здоровые продукты:**\n\n• Овощи: брокколи, шпинат, морковь\n• Фрукты: яблоки, бананы, ягоды\n• Рыба: лосось, треска\n• Орехи и семечки\n• Крупы: овсянка, гречка, бурый рис\n• Йогурт натуральный\n• Авокадо\n• Оливковое масло",
            "быстро": "⚡ **Для быстрого приготовления:**\n\n• Макароны - 500г\n• Яйца - 10 штук\n• Хлеб для тостов\n• Сосиски - 500г\n• Замороженные овощи\n• Готовые соусы\n• Консервы (тунец, кукуруза)\n• Сыр плавленый\n\n**Идеи:** Яичница, макароны с сосисками, тосты с сыром"
        }

        message_lower = user_message.lower()

        # Ищем ключевые слова
        for keyword, response in simple_responses.items():
            if keyword in message_lower:
                return {
                    "response": response,
                    "products": [],
                    "intent": "simple",
                    "model": "simple_ai"
                }

        # Общий ответ
        response = "🤖 **Я готов помочь!** Попробуйте спросить:\n\n• 'Что нужно для борща?'\n• 'Продукты для завтрака'\n• 'Здоровые продукты'\n• 'Быстрый ужин'\n\nИли задайте любой вопрос о еде и продуктах!"

        return {
            "response": response,
            "products": [],
            "intent": "general",
            "model": "simple_ai"
        }

    def detect_intent(self, user_message: str, ai_response: str) -> str:
        """Определяем намерение пользователя"""
        message_lower = user_message.lower()

        recipe_keywords = ['рецепт', 'приготовить', 'готовить', 'как сделать', 'ингредиенты']
        shopping_keywords = ['купить', 'нужно', 'список', 'добавь', 'продукты']
        advice_keywords = ['совет', 'помогите', 'как лучше', 'что выбрать']

        if any(keyword in message_lower for keyword in recipe_keywords):
            return "recipe"
        elif any(keyword in message_lower for keyword in shopping_keywords):
            return "shopping"
        elif any(keyword in message_lower for keyword in advice_keywords):
            return "advice"
        else:
            return "general"

    # Для обратной совместимости
    async def get_shopping_suggestions(self, user_message: str, current_list: List[str] = None) -> str:
        """Простая версия для обратной совместимости"""
        result = await self.get_smart_response(user_message, current_list)
        return result["response"]


# Глобальный экземпляр клиента
perplexity_client = PerplexityClient()
