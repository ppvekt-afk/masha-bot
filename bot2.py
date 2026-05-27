#!/usr/bin/env python3
import logging
import threading
from flask import Flask, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import config
from ai_manager import AIAgent
from handlers import start, help_command, reset, handle_message
from utils import setup_logging

logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return jsonify({"status": "alive", "service": "masha-bot"})

@flask_app.route('/health')
def health_check():
    return jsonify({"status": "ok"})

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

def main():
    setup_logging(config.LOG_LEVEL)
    logger.info("Запуск бота Маша (OpenRouter)")
    
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Ошибка: {e}")
        return
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask сервер запущен на порту 8080")
    
    ai_agent = AIAgent(config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL)
    
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data['ai_agent'] = ai_agent
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Маша запущена через OpenRouter!")
    application.run_polling()

if __name__ == "__main__":
    main()
