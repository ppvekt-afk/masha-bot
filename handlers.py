import logging
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes
from ai_manager import STYLE_PROMPTS

logger = logging.getLogger(__name__)

class UserSession:
    def __init__(self, max_history: int = 15):
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

def get_session(user_id: int, max_history: int = 15) -> UserSession:
    if user_id not in sessions:
        sessions[user_id] = UserSession(max_history)
    return sessions[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 *Маша, главный редактор, приветствует тебя!\n\n"
        "Я — твой личный помощник в мире текстов.\n\n"
        "*/help* — список команд\n"
        "*/reset* — сбросить историю\n\n"
        "Просто напиши мне что-нибудь! ✨",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    styles_list = "\n".join([f"• {s}" for s in STYLE_PROMPTS.keys()])
    await update.message.reply_text(
        f"*Команды:*\n/start — приветствие\n/help — справка\n/reset — сброс истории\n\n"
        f"*Смена стиля:* напиши «в стиле блога», «официально-деловым», «детским», «ироничным»\n\n"
        f"*Доступные стили:*\n{styles_list}\n\n"
        f"*Вернуть обычный стиль:* «верни обычный стиль»",
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_session(user_id).clear()
    if hasattr(context.bot_data, 'ai_agent'):
        context.bot_data['ai_agent'].set_style("default")
    await update.message.reply_text("🧹 История диалога очищена!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    ai_agent = context.bot_data.get('ai_agent')
    
    if not ai_agent:
        await update.message.reply_text("🔧 Технические работы. Загляни чуть позже!")
        return
    
    lower_text = user_text.lower()
    style_detected = None
    
    for style in STYLE_PROMPTS.keys():
        if f"в стиле {style}" in lower_text or f"стиль {style}" in lower_text:
            style_detected = style
            break
    
    if "верни обычный стиль" in lower_text or "стандартный стиль" in lower_text:
        ai_agent.set_style("default")
        await update.message.reply_text("✅ Возвращаюсь к обычному стилю!")
        return
    
    if style_detected:
        ai_agent.set_style(style_detected)
        await update.message.reply_text(f"🎭 Переключаюсь на стиль «{style_detected}»!")
        return
    
    session = get_session(user_id, context.bot_data.get('max_history', 15))
    history = session.get_history()
    session.add_message("user", user_text)
    
    await update.message.chat.send_action(action="typing")
    response = await ai_agent.generate_response(user_text, history)
    session.add_message("assistant", response)
    await update.message.reply_text(response)
