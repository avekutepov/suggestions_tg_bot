from telebot import types
from ..config import Settings

def register_handlers(bot):
    @bot.message_handler(commands=['id'])
    def show_id(message: types.Message):
        bot.send_message(message.chat.id, f"chat_id: {message.chat.id}")

    @bot.message_handler(commands=["help"])
    def on_help(message):
        managers_chat_id = Settings.managers_chat_id
        if not managers_chat_id or message.chat.id != managers_chat_id:
            return

        text = (
            "📖 Доступные команды для менеджеров:\n\n"
            "/weekly – заявки в работе за последние 7 дней\n"
            "/monthly – заявки в работе за последние 30 дней\n"
            "/help – показать это сообщение\n"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")

