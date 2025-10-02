import os
import telebot
from telebot import apihelper
from .config import Settings
from .handlers import register_all
from .db import init_db
from .services.autoreminder import start_weekly_public_reminder

bot = telebot.TeleBot(Settings.bot_token)

# Разовый резолв ID по username (если задан)
PUBLIC_CHAT_USERNAME = os.getenv("PUBLIC_CHAT_USERNAME")  # например, @my_staff_group
if PUBLIC_CHAT_USERNAME:
    try:
        chat = bot.get_chat(PUBLIC_CHAT_USERNAME)
        Settings.public_chat_id = chat.id
        print("Resolved PUBLIC_CHAT_ID =", Settings.public_chat_id)
    except apihelper.ApiTelegramException as e:
        print("get_chat(PUBLIC_CHAT_USERNAME) failed:", e)

register_all(bot)

start_weekly_public_reminder(bot, weekday=1, hour=10, minute=0)

if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
