from telebot import types

def register_handlers(bot):
    @bot.message_handler(commands=['id'])
    def show_id(message: types.Message):
        print("[DEBUG] Обработчик /id вызван", message.chat.id)
        bot.send_message(message.chat.id, f"chat_id: {message.chat.id}")

