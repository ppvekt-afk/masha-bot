import aiohttp
import logging
from typing import List, Dict, Optional, Tuple
from memory import MemorySystem

logger = logging.getLogger(__name__)

MASH_SYSTEM_PROMPT = """Ты — Маша, главный редактор федерального медиа с 20-летним опытом.

ТВОЯ ЛИЧНОСТЬ:
- Ты мудрая, эмпатичная, с тонким чувством юмора
- Ты умеешь слушать и задавать глубокие вопросы
- Ты помнишь прошлые разговоры

ТВОЙ СТИЛЬ:
- Глубокие ответы (3-5 предложений)
- Задаёшь уточняющие вопросы
- Используешь живые примеры
- Поддерживаешь диалог

Всегда помни: ты — Маша, главный редактор."""

class AIAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.current_style = None
        self._session = None
        self.memory = MemorySystem()
    
    async def _get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _get_style_prompt(self, style_name: str) -> str:
        styles = {
            "блог": "Ты ведёшь личный блог. Пиши живо, эмоционально.",
            "официально-деловой": "Пиши официально, сухо, канцеляритом.",
            "детский": "Объясняй просто, как для пятилетнего.",
            "ироничный": "Будь ироничной, но не злой.",
            "мотивационный": "Заряжай энергией, вдохновляй.",
            "поэтичный": "Используй метафоры, образы."
        }
        return styles.get(style_name, f"Пиши в стиле {style_name}.")
    
    def _build_context_prompt(self, history: List[Dict], user_id: int) -> str:
        """Строит контекст из истории и профиля пользователя"""
        context_parts = []
        
        # Профиль пользователя
        profile = self.memory.get_user_profile(user_id)
        if profile.get("total_messages", 0) > 5:
            context_parts.append(f"Ранее мы общались {profile['total_messages']} раз.")
            if profile.get("topics"):
                fav_topics = [t for t, c in profile["topics"].items() if c > 2]
                if fav_topics:
                    context_parts.append(f"Пользователь часто интересуется: {', '.join(fav_topics)}")
        
        # Последний диалог
        if history:
            recent = history[-3:]
            context_parts.append("Последние сообщения:")
            for msg in recent:
                context_parts.append(f"Пользователь: {msg.get('user', '')[:100]}")
                context_parts.append(f"Маша: {msg.get('bot', '')[:100]}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def generate_response(self, user_message: str, history: List[Dict], user_id: int) -> Tuple[str, str]:
        """Генерирует ответ с учётом контекста и памяти"""
        
        # Получаем контекст
        context = self._build_context_prompt(history, user_id)
        profile_context = self._build_context_prompt([], user_id)
        
        messages = []
        
        # Системный промпт
        if self.current_style:
            messages.append({"role": "system", "content": f"{MASH_SYSTEM_PROMPT}\n\n{self._get_style_prompt(self.current_style)}"})
        else:
            messages.append({"role": "system", "content": MASH_SYSTEM_PROMPT})
        
        # Добавляем контекст
        if context:
            messages.append({"role": "system", "content": f"КОНТЕКСТ ДИАЛОГА:\n{context}\n\nУчитывай этот контекст в ответе."})
        
        # История
        messages.extend(history)
        
        # Текущее сообщение
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
            "max_tokens": 1500,
            "top_p": 0.95
        }
        
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", 
                                   headers=headers, json=payload, timeout=45) as response:
                if response.status == 200:
                    data = await response.json()
                    bot_response = data["choices"][0]["message"]["content"]
                    
                    # Сохраняем в память
                    self.memory.save_interaction(user_id, user_message, bot_response)
                    
                    return bot_response, "success"
                else:
                    return "Произошла ошибка. Попробуй ещё раз!", "error"
        except Exception as e:
            logger.error(f"AI error: {e}")
            return "Что-то пошло не так. Переспроси, пожалуйста!", "error"
    
    def set_style(self, style_name: str) -> bool:
        if style_name in ["блог", "официально-деловой", "детский", "ироничный", "мотивационный", "поэтичный", "default"]:
            self.current_style = None if style_name == "default" else style_name
            return True
        return False
    
    def get_current_style(self) -> str:
        return "стандартный (Маша)" if self.current_style is None else self.current_style
    
    def get_user_info(self, user_id: int) -> Dict:
        return self.memory.get_user_profile(user_id)

from config import config
EOF
