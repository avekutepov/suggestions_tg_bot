from telebot import types
from ..config import Settings
from ..keyboards.common import kb_dm_link  # ← добавили

PUBLIC_CHAT_ID = Settings.public_chat_id

def register_handlers(bot):
    me = bot.get_me()
    bot_username = me.username

    @bot.message_handler(content_types=['new_chat_members'])
    def on_new_members(message: types.Message):
        if message.chat.id != PUBLIC_CHAT_ID:
            return

        for user in message.new_chat_members or []:
            if user.is_bot:
                continue
            mention = f'<a href="tg://user?id={user.id}">{user.first_name or "участник"}</a>'
            text = (
                f"👋 {mention}, добро пожаловать!\n\n"
                "Если есть идея или предложение — отправьте его анонимно этому боту в ЛС."
            )
            bot.send_message(
                chat_id=message.chat.id,
                text=text,
                parse_mode="HTML",
                reply_markup=kb_dm_link(bot_username)  # ← используем
            )