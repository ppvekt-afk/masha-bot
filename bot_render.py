#!/usr/bin/env python3
import logging
import threading
import time
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config
from utils import setup_logging
from ai_manager import AIAgent
from handlers import start, help_command, styles_command, style_command, reset, get_session

setup_logging(config.LOG_LEVEL)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return jsonify({"status": "alive", "service": "masha-bot"})

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

BOT_USERNAME = "editorinchief_masha_bot"
BOT_NAME = "Маша"

MODE_EDITOR = "editor"
MODE_CONVERSATION = "conversation"
user_modes = {}

def is_addressed_to_me(update: Update) -> bool:
    if not update.message:
        return False
    text = update.message.text or ""
    if f"@{BOT_USERNAME}" in text or "маша" in text.lower():
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
    await update.message.reply_text("📝 Режим редактора включён.")

async def conversation_mode(update: Update, context):
    if not is_addressed_to_me(update):
        return
    user_id = update.effective_user.id
    user_modes[user_id] = MODE_CONVERSATION
    await update.message.reply_text("💬 Режим общения включён.")

async def smart_mode(update: Update, context):
    if not is_addressed_to_me(update):
        return
    user_id = update.effective_user.id
    user_modes[user_id] = None
    await update.message.reply_text("🧠 Умный режим включён.")

async def handle_message(update: Update, context):
    if not update.message or not update.message.text:
        return
    if not is_addressed_to_me(update):
        return
    
    user_id = update.effective_user.id
    user_text = update.message.text
    import re
    user_text = re.sub(f"@{BOT_USERNAME}", "", user_text, flags=re.IGNORECASE)
    user_text = re.sub(r'\bмаша\b', "", user_text, flags=re.IGNORECASE)
    user_text = user_text.strip()
    
    if not user_text:
        await update.message.reply_text(f"Да, {BOT_NAME} здесь! Чем могу помочь?")
        return
    
    mode = user_modes.get(user_id)
    ai_agent: AIAgent = context.bot_data.get('ai_agent')
    if not ai_agent:
        await update.message.reply_text("Технические работы.")
        return
    
    if mode == MODE_EDITOR or (mode is None and any(w in user_text.lower() for w in ["отредактируй", "исправь", "проверь"])):
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
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    
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
    print(f"{BOT_NAME} ЗАПУЩЕНА с HTTP health-check сервером")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
