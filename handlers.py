import logging
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes

from ai_manager import AIAgent
from memory import MemorySystem

logger = logging.getLogger(__name__)

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
memory = MemorySystem()

def get_session(user_id: int) -> UserSession:
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Обновляем информацию о пользователе
    memory.update_user_info(user_id, {"name": user_name})
    
    profile = memory.get_user_profile(user_id)
    total_msgs = profile.get("total_messages", 0)
    
    if total_msgs == 0:
        text = f"""📝 *Маша, главный редактор, приветствует тебя, {user_name}!*

Я не просто бот — я твой личный редактор и собеседник. 
Я помню наши разговоры, учусь на них и становлюсь лучше.

*Что я умею:*
• Глубоко анализировать тексты
• Вести осмысленный диалог
• Помнить контекст (20+ сообщений)
• Давать редакторские советы
• Учиться на наших разговорах

*Команды:*
/help — список команд
/reset — сбросить историю
/profile — что я о тебе знаю
/topic — сменить тему разговора

Расскажи, с чем тебе помочь? Я внимательно слушаю. ✨"""
    else:
        text = f"""📝 *С возвращением, {user_name}!*

Я помню наши разговоры. Рада снова тебя видеть.

Чем сегодня займёмся? Редактируем текст, ищем вдохновение или просто болтаем?"""
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📚 *Маша — помощь и возможности*

*Команды:*
/start — приветствие
/help — эта справка
/reset — сбросить историю диалога
/profile — что я запомнила о тебе
/topic — предложи тему для обсуждения

*Как я работаю:*
• Помню последние 20 сообщений
• Учитываю историю наших разговоров
• Учусь на твоих реакциях
• Меняю стиль по запросу

*Смена стиля:* 
«Напиши в стиле блога»
«Будь официально-деловой»
«Расскажи как для детей»

*Секрет:* Чем больше мы общаемся, тем лучше я тебя понимаю.

Чего бы тебе хотелось сегодня?"""
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = memory.get_user_profile(user_id)
    
    if profile.get("total_messages", 0) == 0:
        text = "📭 Я ещё мало о тебе знаю. Поговори со мной, и я запомню больше!"
    else:
        text = f"""📊 *Что я знаю о тебе*

• Общаемся: {profile['total_messages']} сообщений
• Впервые пришёл: {profile.get('first_seen', 'недавно')[:16]}

*Твои интересы:*"""
        
        if profile.get("topics"):
            for topic, count in profile["topics"].items():
                text += f"\n  • {topic}: {count} раз"
        else:
            text += "\n  • Пока не определились"
        
        text += "\n\n*Совет:* Чем больше мы общаемся, тем глубже я тебя понимаю."
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def topic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🎯 *О чём хочешь поговорить?*

Выбери тему или предложи свою:
• Редактура текста
• Написание статей
• Советы по стилю
• Вдохновение и идеи
• Книги и чтение
• Просто поболтать

Напиши тему, и начнём!"""
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)
    session.clear()
    
    await update.message.reply_text(
        "🧹 История диалога очищена.\n"
        "Но я помню наш общий контекст — это в моей долговременной памяти.\n\n"
        "Начнём с чистого листа?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    ai_agent: AIAgent = context.bot_data.get('ai_agent')
    
    if not ai_agent:
        await update.message.reply_text("🔧 Технические работы. Загляни чуть позже!")
        return
    
    # Смена стиля
    lower_text = user_text.lower()
    styles = ["блог", "официально-деловой", "детский", "ироничный", "мотивационный", "поэтичный"]
    
    for style in styles:
        if f"в стиле {style}" in lower_text or f"стиль {style}" in lower_text:
            ai_agent.set_style(style)
            await update.message.reply_text(f"🎭 Хорошо! Переключаюсь на стиль «{style}».")
            return
    
    if "верни обычный стиль" in lower_text or "стандартный стиль" in lower_text:
        ai_agent.set_style("default")
        await update.message.reply_text("✅ Возвращаюсь к обычному стилю.")
        return
    
    # Получаем историю
    session = get_session(user_id)
    history = session.get_history()
    
    # Добавляем сообщение
    session.add_message("user", user_text)
    
    # Индикатор печати
    await update.message.chat.send_action(action="typing")
    
    # Генерируем ответ
    response, status = await ai_agent.generate_response(user_text, history, user_id)
    
    # Добавляем ответ в историю
    session.add_message("assistant", response)
    
    # Отправляем ответ
    await update.message.reply_text(response)

from config import config
EOF        "*/reset* — сбросить историю\n\n"
        "Просто напиши мне что-нибудь! ✨",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    styles_list = "\n".join([f"• {s}" for s in STYLE_PROMPTS.keys()])
    await update.message.reply_text(
        f"*Команды:*\n/start — приветствие\n/help — справка\n/reset — сброс истории\n\n"
        f"*Смена стиля:* напиши «в стиле блога», «официально-деловым», «детским», «ироничным»\n\n"
        f"*Доступные стили:*\n{styles_list}\n\n"
        f"*Вернуть обычный стиль:* «верни обычный стиль»",
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
