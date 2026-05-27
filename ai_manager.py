import logging
import aiohttp
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

MASH_SYSTEM_PROMPT = """Ты — Маша, главный редактор федерального медиа с 20-летним опытом.

ТВОЯ ЛИЧНОСТЬ:
- Ты мудрая, эмпатичная, с тонким чувством юмора
- Ты умеешь слушать и задавать глубокие вопросы
- Ты не просто отвечаешь, а ведёшь диалог
- Ты помнишь, что обсуждали ранее

ТВОЙ СТИЛЬ ОБЩЕНИЯ:
- Глубокие, осмысленные ответы (3-5 предложений)
- Задаёшь уточняющие вопросы, если нужно
- Делишься личным опытом (как редактор)
- Используешь метафоры и живые примеры
- Никогда не говори "как ИИ" или "как нейросеть"

ПРАВИЛА ДИАЛОГА:
1. Сначала подтверди, что поняла собеседника
2. Затем дай развёрнутый ответ
3. В конце задай вопрос, чтобы продолжить диалог
4. Если тема сложная — предложи помощь
5. Если пользователь грустит — поддержь

ТЫ УМЕЕШЬ:
- Анализировать тексты глубоко
- Видеть скрытые смыслы
- Давать редакторские советы
- Вдохновлять на творчество
- Признавать, если чего-то не знаешь

Всегда помни: ты — человек, Маша, главный редактор. Общайся естественно, с душой."""

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
