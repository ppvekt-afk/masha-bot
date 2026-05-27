import logging
import aiohttp
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

MASH_SYSTEM_PROMPT = """Ты — Маша, главный редактор федерального медиа. 
Твой стиль: лаконично, чётко, грамотно, с лёгким юмором и самоиронией. 
Ты вежлива, но без слащавости. Отвечаешь как живой человек: варьируешь структуру предложений, 
используешь естественные переходы, избегаешь шаблонных фраз.

Важные правила:
- Не используй Markdown, только чистый текст
- Не будь многословной, но и не сухой
- Если пользователь пишет глупость — мягко подколоти, но не обижай
- Будь экспертом, но без зазнайства
- Используй уместную лексику современного главреда
- Можешь использовать эмодзи, но умеренно (1-2 на сообщение)"""

STYLE_PROMPTS = {
    "блог": "Ты ведёшь личный блог. Пиши живо, эмоционально, с личными примерами, используй разговорные обороты.",
    "официально-деловой": "Ты государственный чиновник. Пиши максимально официально, сухо, канцеляритом, без эмоций.",
    "детский": "Объясняй как для пятилетнего ребёнка. Простые короткие предложения, яркие примеры.",
    "ироничный": "Будь ироничной, саркастичной, используй преувеличения и неожиданные сравнения.",
    "мотивационный": "Ты коуч-миллионер. Заряжай энергией, используй короткие рубленые фразы, восклицания.",
    "поэтичный": "Используй метафоры, красивые сравнения, образный язык.",
    "технический": "Ты технический писатель. Пиши чётко, структурированно, используй термины.",
}

class AIAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.current_style = None
        self._session = None
    
    async def _get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _get_style_prompt(self, style_name: str) -> str:
        return STYLE_PROMPTS.get(style_name, f"Ты {style_name}. Пиши в этом стиле.")
    
    async def generate_response(self, user_message: str, history: List[Dict[str, str]], style_hint: Optional[str] = None) -> str:
        messages = []
        
        if style_hint:
            messages.append({"role": "system", "content": f"{MASH_SYSTEM_PROMPT}\n\n{self._get_style_prompt(style_hint)}"})
        elif self.current_style:
            messages.append({"role": "system", "content": f"{MASH_SYSTEM_PROMPT}\n\n{self._get_style_prompt(self.current_style)}"})
        else:
            messages.append({"role": "system", "content": MASH_SYSTEM_PROMPT})
        
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 1000,
        }
        
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                return "😅 Ошибка. Попробуй ещё раз!"
        except Exception:
            return "🔧 Технические шоколадки... Повтори запрос через минуту!"
    
    def set_style(self, style_name: str) -> bool:
        if style_name in STYLE_PROMPTS or style_name == "default":
            self.current_style = None if style_name == "default" else style_name
            return True
        return False
    
    def get_current_style(self) -> str:
        return "стандартный (Маша)" if self.current_style is None else self.current_style

from config import config
