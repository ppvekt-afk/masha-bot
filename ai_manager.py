import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

MASH_SYSTEM_PROMPT = """Ты — Маша, главный редактор федерального медиа. Отвечай живо, грамотно, с лёгким юмором. Не используй Markdown."""

class AIAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.current_style = None
        self._session = None

    async def _get_session(self):
        if self._session is None:
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    def _get_style_prompt(self, style_name: str) -> str:
        styles = {
            "блог": "Пиши живо, эмоционально, как в личном блоге.",
            "официально-деловой": "Пиши официально, сухо, канцеляритом.",
            "детский": "Объясняй просто, как для пятилетнего.",
            "ироничный": "Будь ироничной, но не злой.",
            "мотивационный": "Заряжай энергией, вдохновляй."
        }
        return styles.get(style_name, f"Пиши в стиле {style_name}.")

    async def generate_response(self, user_message: str, history: List[Dict], user_id: int) -> Tuple[str, str]:
        messages = []
        
        if self.current_style:
            messages.append({"role": "system", "content": f"{MASH_SYSTEM_PROMPT}\n\n{self._get_style_prompt(self.current_style)}"})
        else:
            messages.append({"role": "system", "content": MASH_SYSTEM_PROMPT})
        
        if history:
            messages.extend(history[-10:])
        
        messages.append({"role": "user", "content": user_message})
        
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 1500
        }
        
        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
                ssl=False
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"], "success"
                elif response.status == 429:
                    return "Слишком много запросов. Подожди 10 секунд и попробуй ещё раз!", "error"
                else:
                    error_text = await response.text()
                    logger.error(f"API Error {response.status}: {error_text}")
                    return f"Ошибка API: {response.status}. Попробуй ещё раз!", "error"
        except asyncio.TimeoutError:
            return "Сервер не отвечает. Попробуй ещё раз!", "error"
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            return "🔧 Технические шоколадки... Повтори запрос через минуту!", "error"

    def set_style(self, style_name: str) -> bool:
        styles = ["блог", "официально-деловой", "детский", "ироничный", "мотивационный", "default"]
        if style_name in styles:
            self.current_style = None if style_name == "default" else style_name
            return True
        return False

    def get_current_style(self) -> str:
        return "стандартный (Маша)" if self.current_style is None else self.current_style

from config import config
