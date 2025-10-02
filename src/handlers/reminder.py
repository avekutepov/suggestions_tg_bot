from telebot import types
from ..config import Settings
from .. services.autoreminder import _send_reminder

def register_handlers(bot):
    @bot.message_handler(commands=["remind"])
    def manual_reminder(message: types.Message):
        if message.chat.id != Settings.managers_chat_id:
            return
        _send_reminder(bot)
        bot.reply_to(message, "✅ Напоминание отправлено в общую группу")