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

BOT_USERNAME = "masha_editor_bot"
BOT_NAME = "Маша"

def is_mentioned(update: Update) -> bool:
    if not update.message:
        return False
    text = update.message.text or ""
    if f"@{BOT_USERNAME}" in text:
        return True
    if update.message.reply_to_message:
        reply_to = update.message.reply_to_message
        if reply_to.from_user and reply_to.from_user.is_bot:
            if reply_to.from_user.username == BOT_USERNAME:
                return True
    if update.message.chat.type == "private":
        return True
    return False

async def start_command(update: Update, context):
    if not is_mentioned(update):
        return
    await start(update, context)

async def help_command_group(update: Update, context):
    if not is_mentioned(update):
        return
    await help_command(update, context)

async def styles_command_group(update: Update, context):
    if not is_mentioned(update):
        return
    await styles_command(update, context)

async def style_command_group(update: Update, context):
    if not is_mentioned(update):
        return
    await style_command(update, context)

async def reset_command_group(update: Update, context):
    if not is_mentioned(update):
        return
    await reset(update, context)

async def handle_message(update: Update, context):
    if not is_mentioned(update):
        return
    
    user_text = update.message.text or ""
    user_text = re.sub(f"@{BOT_USERNAME}", "", user_text).strip()
    user_text = re.sub(f"{BOT_NAME}", "", user_text, flags=re.IGNORECASE).strip()
    
    if not user_text:
        return
    
    ai_agent: AIAgent = context.bot_data.get('ai_agent')
    if not ai_agent:
        await update.message.reply_text("Технические работы.")
        return
    
    user_id = update.effective_user.id
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 50)
    print(f"МАША ЗАПУЩЕНА (режим группы)")
    print(f"Отвечает на упоминания: @{BOT_USERNAME}")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
