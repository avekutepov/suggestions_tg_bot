from telebot import types
from ..config import Settings
from ..keyboards.common import kb_moderation_final
from ..db import set_status

try:
    from ..db import get_suggestion
except Exception:
    get_suggestion = None

MANAGERS_CHAT_ID = Settings.managers_chat_id

def register_handlers(bot):

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("moder:"))
    def on_moder(call: types.CallbackQuery):

        msg = call.message
        parts = call.data.split(":")
        if len(parts) != 3:
            bot.answer_callback_query(call.id)
            return

        _, action, id_str = parts
        try:
            sugg_id = int(id_str)
        except ValueError:
            bot.answer_callback_query(call.id)
            return

        # Проверка на повтор (теперь учитываем in_process вместо approved)
        if get_suggestion:
            try:
                s = get_suggestion(sugg_id)
                if s and s.get("status") in {"in_process", "rejected"}:
                    bot.answer_callback_query(call.id, "Уже обработано", show_alert=False)
                    return
            except Exception as e:
                print(f"[moderation] get_suggestion failed: {e}")

        if action == "ok":
            # статус вместо approved → in_process
            set_status(sugg_id, "in_process")
            try:
                bot.edit_message_reply_markup(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    reply_markup=kb_moderation_final("✅ Принято")
                )
            except Exception as e:
                print(f"[moderation] edit_message_reply_markup(ok) failed: {e}")
            bot.answer_callback_query(call.id, "Принято", show_alert=False)

            if get_suggestion:
                try:
                    s = get_suggestion(sugg_id)
                    uid = s and s.get("user_id")
                    if uid:
                        bot.send_message(uid, f"✅ Ваша заявка #{sugg_id} взята на рассмотрение руководством.")
                except Exception as e:
                    print(f"[moderation] notify user(ok) failed: {e}")

        elif action == "rej":
            set_status(sugg_id, "rejected")
            try:
                bot.edit_message_reply_markup(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    reply_markup=kb_moderation_final("🚫 Отклонено")
                )
            except Exception as e:
                print(f"[moderation] edit_message_reply_markup(rej) failed: {e}")
            bot.answer_callback_query(call.id, "Отклонено", show_alert=False)

            if get_suggestion:
                try:
                    s = get_suggestion(sugg_id)
                    uid = s and s.get("user_id")
                    if uid:
                        bot.send_message(uid, f"🚫 Ваша заявка #{sugg_id} отклонена.\nПричина: не соответствует требованиям.")
                except Exception as e:
                    print(f"[moderation] notify user(rej) failed: {e}")
        else:
            bot.answer_callback_query(call.id)
