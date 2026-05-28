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

conversation_mode = False

def is_direct_mention(update: Update) -> bool:
    if not update.message:
        return False
    
    message = update.message
    text = message.text or ""
    
    if f"@{BOT_USERNAME}" in text:
        return True
    
    if message.reply_to_message:
        if message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot:
            if message.reply_to_message.from_user.username == BOT_USERNAME:
                return True
    
    if message.chat.type == "private":
        return True
    
    return False

def is_bot_addressed_to_me(update: Update) -> bool:
    if not update.message:
        return False
    
    text = update.message.text or ""
    reply_to = update.message.reply_to_message
    
    if reply_to and reply_to.from_user and reply_to.from_user.is_bot:
        if f"@{BOT_USERNAME}" in text:
            return True
    
    return False

async def start_command(update: Update, context):
    if not is_direct_mention(update):
        return
    await start(update, context)
    await update.message.reply_text(
        f"Команды:\n"
        f"/talk_on — включить режим диалога с другими ботами\n"
        f"/talk_off — выключить режим диалога"
    )

async def help_command_group(update: Update, context):
    if not is_direct_mention(update):
        return
    await help_command(update, context)

async def styles_command_group(update: Update, context):
    if not is_direct_mention(update):
        return
    await styles_command(update, context)

async def style_command_group(update: Update, context):
    if not is_direct_mention(update):
        return
    await style_command(update, context)

async def reset_command_group(update: Update, context):
    if not is_direct_mention(update):
        return
    await reset(update, context)

async def talk_on(update: Update, context):
    global conversation_mode
    if not is_direct_mention(update):
        return
    conversation_mode = True
    await update.message.reply_text(f"🗣️ Режим диалога включён. Теперь я буду отвечать другим ботам.")

async def talk_off(update: Update, context):
    global conversation_mode
    if not is_direct_mention(update):
        return
    conversation_mode = False
    await update.message.reply_text(f"🔇 Режим диалога выключен. Я отвечаю только на прямые упоминания.")

async def handle_message(update: Update, context):
    global conversation_mode
    
    if not update.message or not update.message.text:
        return
    
    if is_direct_mention(update):
        user_text = update.message.text
        user_text = re.sub(f"@{BOT_USERNAME}", "", user_text, flags=re.IGNORECASE)
        user_text = user_text.strip()
        
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
        return
    
    if conversation_mode and is_bot_addressed_to_me(update):
        user_text = update.message.text
        user_text = re.sub(f"@{BOT_USERNAME}", "", user_text, flags=re.IGNORECASE)
        user_text = user_text.strip()
        
        if not user_text:
            return
        
        ai_agent: AIAgent = context.bot_data.get('ai_agent')
        if not ai_agent:
            return
        
        response, status = await ai_agent.generate_response(user_text, [], 0)
        await update.message.reply_text(response)
        return
    
    return

def main():
    ai_agent = AIAgent(config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL)
    
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.bot_data['ai_agent'] = ai_agent
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command_group))
    app.add_handler(CommandHandler("styles", styles_command_group))
    app.add_handler(CommandHandler("style", style_command_group))
    app.add_handler(CommandHandler("reset", reset_command_group))
    app.add_handler(CommandHandler("talk_on", talk_on))
    app.add_handler(CommandHandler("talk_off", talk_off))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 50)
    print(f"{BOT_NAME} ЗАПУЩЕНА")
    print(f"Реагирует на: @{BOT_USERNAME}")
    print("Режим диалога: выключен (включите /talk_on)")
    print("=" * 50)
    
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
