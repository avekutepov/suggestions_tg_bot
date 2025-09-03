from telebot import types, apihelper
from ..config import Settings

PUBLIC_CHAT_ID = Settings.public_chat_id

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def on_start(message: types.Message):
        if message.chat.type != "private":
            return
        try:
            member = bot.get_chat_member(PUBLIC_CHAT_ID, message.from_user.id)
            if member.status in ("left", "kicked"):
                bot.send_message(
                    message.chat.id,
                    "🛡️ Доступ только для участников общей группы. Вступите и напишите снова."
                )
                return
        except apihelper.ApiTelegramException as e:
            print(f"[get_chat_member] failed for chat {PUBLIC_CHAT_ID}, user {message.from_user.id}: {e}")
            bot.send_message(
                message.chat.id,
                "⚠️ Бот не видит общую группу или у него нет прав. Сообщите администратору."
            )
            return

        bot.send_message(message.chat.id, "👋 Привет! Это анонимный бот для предложений.")