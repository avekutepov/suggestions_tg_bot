from telebot import types
from ..config import Settings

PUBLIC_CHAT_ID = Settings.public_chat_id

def register_handlers(bot):

    def publish_from_manager_message(msg: types.Message):
        """
        Опубликовать в PUBLIC_CHAT_ID тот же контент, что пришёл менеджерам,
        + добавить подпись "✅ Одобрено руководством".
        """
        approved_tag = "\n\n✅ <b>Одобрено руководством</b>"

        if msg.photo:
            file_id = msg.photo[-1].file_id
            caption = (msg.caption or "") + approved_tag
            bot.send_photo(PUBLIC_CHAT_ID, file_id, caption=caption, parse_mode="HTML")
        elif msg.document:
            caption = (msg.caption or "") + approved_tag
            bot.send_document(PUBLIC_CHAT_ID, msg.document.file_id, caption=caption, parse_mode="HTML")
        elif msg.video:
            caption = (msg.caption or "") + approved_tag
            bot.send_video(PUBLIC_CHAT_ID, msg.video.file_id, caption=caption, parse_mode="HTML")
        elif msg.voice:
            # у voice caption обычно пустой, поэтому подпись отдельным сообщением
            bot.send_voice(PUBLIC_CHAT_ID, msg.voice.file_id)
            bot.send_message(PUBLIC_CHAT_ID, approved_tag, parse_mode="HTML")
        else:
            text = (msg.text or msg.caption or "") + approved_tag
            bot.send_message(PUBLIC_CHAT_ID, text, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data == "approve")
    def on_approve(call: types.CallbackQuery):
        try:
            publish_from_manager_message(call.message)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Опубликовано")
            bot.reply_to(call.message, "✅ Одобрено и опубликовано в общую группу.")
        except Exception as e:
            bot.answer_callback_query(call.id, "Ошибка публикации")
            bot.reply_to(call.message, f"⚠️ Не удалось опубликовать: {e}")

    @bot.callback_query_handler(func=lambda c: c.data == "reject")
    def on_reject(call: types.CallbackQuery):
        try:
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Отклонено")
            bot.reply_to(call.message, "🚫 Отклонено.")
        except Exception as e:
            bot.answer_callback_query(call.id, "Ошибка")
            bot.reply_to(call.message, f"⚠️ Не удалось изменить статус: {e}")
