# src/handlers/start.py
from telebot import types
from ..keyboards.common import criteria_keyboard

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def on_start(message: types.Message):
        # Обрабатываем ТОЛЬКО ЛС
        if message.chat.type != "private":
            return

        text = (message.text or "").strip()
        parts = text.split(maxsplit=1)
        payload = parts[1].strip().lower() if len(parts) > 1 else ""

        if payload == "suggest":
            # deep-link вида ?start=suggest
            bot.send_message(
                message.chat.id,
                "Выберите категорию вашего предложения:",
                reply_markup=criteria_keyboard()
            )
        else:
            # обычный /start без аргумента — просто приветствие
            bot.send_message(
                message.chat.id,
                "👋 Привет! Нажмите /suggest, чтобы отправить анонимное предложение."
            )
