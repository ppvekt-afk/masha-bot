import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.current_style = None
        self._session = None

    async def _get_session(self):
        if self._session is None:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session

    def _get_style_prompt(self, style_name: str) -> str:
        styles = {
            "редактура": "Ты главный редактор. Отредактируй текст: убери AI-слова, канцелярит, шаблоны. Сделай живым и естественным.",
            "разговорный": "Ты Маша, приятная собеседница. Отвечай как живой человек: коротко, по делу, с душой.",
            "блог": "Пиши как блогер: живо, эмоционально, с восклицаниями.",
            "официально-деловой": "Пиши официально, сухо, по делу.",
            "детский": "Объясняй просто, как пятилетнему.",
            "ироничный": "С мягкой иронией, добрым сарказмом.",
            "мотивационный": "Заряжай энергией, вдохновляй.",
            "академический": "Как научная статья: термины, объективность.",
            "технический": "Чётко, структурированно, с терминами.",
            "поэтический": "Образно, метафорично, красиво.",
            "журналистский": "Факты, короткие абзацы, цепляющий заголовок.",
        }
        return styles.get(style_name, styles.get("разговорный", "Отвечай как человек."))

    async def generate_response(self, user_message: str, history: List[Dict], user_id: int) -> Tuple[str, str]:
        messages = []
        
        if self.current_style:
            style_prompt = self._get_style_prompt(self.current_style)
            messages.append({"role": "system", "content": style_prompt})
        else:
            messages.append({"role": "system", "content": "Ты Маша, главный редактор. Отвечай как человек: без шаблонов и канцелярита."})
        
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
            "max_tokens": 1000
        }
        
        fallback_models = ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku", "meta-llama/llama-3-8b-instruct"]
        
        for model in [self.model] + fallback_models:
            try:
                payload["model"] = model
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        raw_text = data["choices"][0]["message"]["content"]
                        import re
                        raw_text = re.sub(r'\*\*(.+?)\*\*', r'\1', raw_text)
                        raw_text = re.sub(r'\*(.+?)\*', r'\1', raw_text)
                        return raw_text.strip(), "success"
                    elif response.status == 429:
                        await asyncio.sleep(2)
                        continue
                    else:
                        continue
            except asyncio.TimeoutError:
                logger.warning(f"Timeout with model {model}")
                continue
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                continue
        
        return "Извини, сейчас не могу ответить. Попробуй ещё раз.", "error"

    def set_style(self, style_name: str) -> bool:
        styles = ["редактура", "разговорный", "блог", "официально-деловой", "детский", 
                  "ироничный", "мотивационный", "академический", "технический", 
                  "поэтический", "журналистский", "default"]
        if style_name in styles:
            self.current_style = None if style_name == "default" else style_name
            return True
        return False

    def get_current_style(self) -> str:
        return "стандартный" if self.current_style is None else self.current_style
