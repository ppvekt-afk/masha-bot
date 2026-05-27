#!/usr/bin/env python3
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import config
from ai_manager import AIAgent
from handlers import start, help_command, reset, handle_message
from utils import setup_logging

logger = logging.getLogger(__name__)

def main():
    setup_logging(config.LOG_LEVEL)
    logger.info("Запуск бота Маша (bot2.py)")
    
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Ошибка: {e}")
        return
    
    ai_agent = AIAgent(config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL)
    
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data['ai_agent'] = ai_agent
    application.bot_data['max_history'] = config.MAX_HISTORY_LENGTH
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
