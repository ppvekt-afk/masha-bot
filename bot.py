#!/usr/bin/env python3
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config
from ai_manager import AIAgent
from handlers import start, help_command, styles_command, style_command, reset, get_session
from utils import setup_logging

setup_logging(config.LOG_LEVEL)
logger = logging.getLogger(__name__)

BOT_USERNAME = "editorinchief_masha_bot"
BOT_NAME = "Маша"

MODE_EDITOR = "editor"
MODE_CONVERSATION = "conversation"
user_modes = {}

RELATIONSHIP_ADVICE = {
    "i_statements": "Формула я-высказывания: Я чувствую [эмоция], когда [ситуация], потому что [влияние].\nПример: Я чувствую одиночество, когда мы долго не разговариваем, потому что мне важно быть в контакте.",
    "active_listening": "Активное слушание:\n• Отрази: 'Я слышу, что ты говоришь...'\n• Подтверди: 'Это понятно, потому что...'\n• Уточни: 'Ты имеешь в виду...?'\n• Не готовь ответ, пока слушаешь.",
    "boundaries": "Границы в общении:\n• Чётко назови свою потребность\n• Без оправданий: 'Мне сейчас нужно 10 минут тишины'\n• Предложи альтернативу: 'Можем обсудить это через час?'",
}

def is_addressed_to_me(update: Update) -> bool:
    if not update.message:
        return False
    text = update.message.text or ""
    if f"@{BOT_USERNAME}" in text or "маша" in text.lower():
        return True
    if update.message.reply_to_message and update.message.reply_to_message.from_user and update.message.reply_to_message.from_user.is_bot:
        if update.message.reply_to_message.from_user.username == BOT_USERNAME:
            return True
    if update.message.chat.type == "private":
        return True
    return False

async def start_command(update: Update, context):
    if not is_addressed_to_me(update):
        return
    user_id = update.effective_user.id
    user_modes[user_id] = MODE_EDITOR
    await start(update, context)
    await update.message.reply_text(
        f"Обращаться ко мне можно:\n• @{BOT_USERNAME}\n• {BOT_NAME}\n\n"
        f"Режимы:\n/editor_mode — только редактура\n/conversation_mode — живое общение\n/smart_mode — сама определю\n\n"
        f"Я могу помочь с отношениями, конфликтами, свиданиями, общением. Спроси меня, как улучшить отношения или как помириться."
    )

async def help_command_group(update: Update, context):
    if not is_addressed_to_me(update):
        return
    await help_command(update, context)

async def styles_command_group(update: Update, context):
    if not is_addressed_to_me(update):
        return
    await styles_command(update, context)

async def style_command_group(update: Update, context):
    if not is_addressed_to_me(update):
        return
    await style_command(update, context)

async def reset_command_group(update: Update, context):
    if not is_addressed_to_me(update):
        return
    await reset(update, context)

async def editor_mode(update: Update, context):
    if not is_addressed_to_me(update):
        return
    user_id = update.effective_user.id
    user_modes[user_id] = MODE_EDITOR
    await update.message.reply_text("📝 Режим редактора: редактирую тексты, исправляю ошибки, улучшаю стиль.")

async def conversation_mode(update: Update, context):
    if not is_addressed_to_me(update):
        return
    user_id = update.effective_user.id
    user_modes[user_id] = MODE_CONVERSATION
    await update.message.reply_text("💬 Режим общения: могу поговорить на любые темы — отношения, чувства, планы, литература, жизнь.")

async def smart_mode(update: Update, context):
    if not is_addressed_to_me(update):
        return
    user_id = update.effective_user.id
    user_modes[user_id] = None
    await update.message.reply_text("🧠 Умный режим: сама определю, нужна редактура или живое общение.")

async def handle_message(update: Update, context):
    if not update.message or not update.message.text:
        return
    if not is_addressed_to_me(update):
        return
    
    user_id = update.effective_user.id
    user_text = update.message.text
    user_text = re.sub(f"@{BOT_USERNAME}", "", user_text, flags=re.IGNORECASE)
    user_text = re.sub(r'\bмаша\b', "", user_text, flags=re.IGNORECASE)
    user_text = user_text.strip()
    
    if not user_text:
        await update.message.reply_text(f"Да, {BOT_NAME} здесь! Чем могу помочь?")
        return
    
    lower = user_text.lower()
    if "i statement" in lower or "я-высказывание" in lower:
        await update.message.reply_text(RELATIONSHIP_ADVICE["i_statements"])
        return
    if "активное слушание" in lower or "active listening" in lower:
        await update.message.reply_text(RELATIONSHIP_ADVICE["active_listening"])
        return
    if "границы" in lower or "boundaries" in lower:
        await update.message.reply_text(RELATIONSHIP_ADVICE["boundaries"])
        return
    if "отношения" in lower or "relationship" in lower:
        await update.message.reply_text("💞 Отношения — это важно. Я могу помочь:\n• Подобрать слова для сложного разговора\n• Предложить идеи для свиданий\n• Помочь помириться после ссоры\n• Просто выслушать и поддержать.\nРасскажи, что случилось?")
        return
    
    mode = user_modes.get(user_id)
    ai_agent: AIAgent = context.bot_data.get('ai_agent')
    if not ai_agent:
        await update.message.reply_text("Технические работы.")
        return
    
    if mode == MODE_EDITOR or (mode is None and any(w in lower for w in ["отредактируй", "исправь", "проверь"])):
        ai_agent.set_style("редактура")
    else:
        ai_agent.set_style("разговорный")
    
    session = get_session(user_id)
    history = session.get_history()
    session.add_message("user", user_text)
    
    await update.message.chat.send_action(action="typing")
    response, status = await ai_agent.generate_response(user_text, history, user_id)
    session.add_message("assistant", response)
    await update.message.reply_text(response)

def main():
    ai_agent = AIAgent(config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL)
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.bot_data['ai_agent'] = ai_agent
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command_group))
    app.add_handler(CommandHandler("styles", styles_command_group))
    app.add_handler(CommandHandler("style", style_command_group))
    app.add_handler(CommandHandler("reset", reset_command_group))
    app.add_handler(CommandHandler("editor_mode", editor_mode))
    app.add_handler(CommandHandler("conversation_mode", conversation_mode))
    app.add_handler(CommandHandler("smart_mode", smart_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 50)
    print(f"{BOT_NAME} ЗАПУЩЕНА")
    print(f"Реагирует на: @{BOT_USERNAME}, {BOT_NAME}")
    print("Режимы: /editor_mode, /conversation_mode, /smart_mode")
    print("💝 Новые навыки: советы по отношениям, коммуникация, конфликты")
    print("=" * 50)
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
