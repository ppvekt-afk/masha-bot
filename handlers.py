import logging
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes

from ai_manager import AIAgent

logger = logging.getLogger(__name__)

STYLES = {
    "блог": "Личный блог",
    "официально-деловой": "Официально-деловой",
    "детский": "Детский",
    "ироничный": "Ироничный",
    "мотивационный": "Мотивационный"
}

class UserSession:
    def __init__(self, max_history: int = 20):
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
    
    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]
    
    def get_history(self) -> List[Dict[str, str]]:
        return self.history.copy()
    
    def clear(self):
        self.history = []

sessions: Dict[int, UserSession] = {}

def get_session(user_id: int) -> UserSession:
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📝 *Маша, главный редактор, приветствует тебя!*

Я — твой личный помощник. Я использую ИИ для анализа и редактирования текстов.

*Команды:*
/start — приветствие
/help — справка
/reset — сбросить историю

*Смена стиля:*
«Напиши в стиле блога»
«Официально-деловым»
«Расскажи как для детей»
«Сделай ироничным»

Просто напиши, с чем тебе помочь! ✨"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📚 *Команды и возможности*

/start — приветствие
/help — справка
/reset — сбросить историю

*Стили общения:*
• блог — живой, эмоциональный
• официально-деловой — строгий, сухой
• детский — простой, игривый
• ироничный — с юмором
• мотивационный — вдохновляющий

*Как сменить стиль:*
Просто напиши фразу вроде:
«Напиши в стиле блога»"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)
    session.clear()
    await update.message.reply_text("🧹 История диалога очищена!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    ai_agent: AIAgent = context.bot_data.get('ai_agent')
    
    if not ai_agent:
        await update.message.reply_text("🔧 Технические работы. Загляни чуть позже!")
        return
    
    lower_text = user_text.lower()
    style_map = {
        "блог": "блог",
        "официально-деловым": "официально-деловой",
        "детским": "детский",
        "ироничным": "ироничный",
        "мотивационным": "мотивационный"
    }
    
    for key, style in style_map.items():
        if key in lower_text or f"в стиле {style}" in lower_text:
            ai_agent.set_style(style)
            await update.message.reply_text(f"🎭 Переключаюсь на стиль «{style}»!")
            return
    
    if "верни обычный стиль" in lower_text or "стандартный стиль" in lower_text:
        ai_agent.set_style("default")
        await update.message.reply_text("✅ Возвращаюсь к обычному стилю!")
        return
    
    session = get_session(user_id)
    history = session.get_history()
    session.add_message("user", user_text)
    
    await update.message.chat.send_action(action="typing")
    response, status = await ai_agent.generate_response(user_text, history, user_id)
    session.add_message("assistant", response)
    await update.message.reply_text(response)

from config import config
