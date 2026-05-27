import logging
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes

from ai_manager import AIAgent

logger = logging.getLogger(__name__)

STYLES = {
    "блог": "Живой блог",
    "официально-деловой": "Официальный документ",
    "детский": "Как для детей",
    "ироничный": "С иронией",
    "мотивационный": "Вдохновляющий",
    "академический": "Научный",
    "технический": "Технический",
    "поэтический": "Поэтический",
    "журналистский": "Журналистский",
    "разговорный": "Разговорный"
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
    text = """📝 Маша, главный редактор.

Режимы:
/editor_mode — редактирую тексты
/conversation_mode — живое общение
/smart_mode — сама определяю

Стили:
/style блог — сменить стиль
/styles — все стили

Команды:
/start — приветствие
/help — справка
/reset — очистить историю

Просто напиши что нужно!"""
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """Команды Маши:

Режимы:
/editor_mode — только редактура
/conversation_mode — живое общение
/smart_mode — автоопределение

Стили:
/style блог — сменить стиль
/styles — все стили

Другое:
/start — приветствие
/reset — очистить историю

Примеры:
• отредактируй этот текст
• что думаешь о литературе?
• /style ироничный"""
    await update.message.reply_text(text)

async def styles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎭 Доступные стили:\n\n"
    for style, desc in STYLES.items():
        text += f"• {style} — {desc}\n"
    text += "\nИспользуй: /style [стиль]"
    await update.message.reply_text(text)

async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args).lower() if context.args else ""
    if not args or args not in STYLES:
        await update.message.reply_text(f"Доступные стили: {', '.join(STYLES.keys())}")
        return
    
    ai_agent: AIAgent = context.bot_data.get('ai_agent')
    if ai_agent:
        ai_agent.set_style(args)
        await update.message.reply_text(f"✅ Стиль изменён: {args}")
    else:
        await update.message.reply_text("Технические работы.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)
    session.clear()
    
    ai_agent: AIAgent = context.bot_data.get('ai_agent')
    if ai_agent:
        ai_agent.set_style("default")
    
    await update.message.reply_text("История очищена.")
