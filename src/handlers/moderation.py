# src/handlers/moderation.py
from telebot import types
from ..config import Settings
from ..keyboards.common import kb_moderation_final
from ..db import set_status

# Опционально подтянем get_suggestion, если оно есть в db.py
try:
    from ..db import get_suggestion  # must return dict with keys: user_id, status, ...
except Exception:
    get_suggestion = None  # уведомление автора отключим, если не доступно

MANAGERS_CHAT_ID = Settings.managers_chat_id

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("moder:"))
    def on_moder(call: types.CallbackQuery):
        # Разрешаем только в менеджерском чате
        msg = call.message
        if not msg or msg.chat.id != MANAGERS_CHAT_ID:
            bot.answer_callback_query(call.id, "Недоступно здесь", show_alert=False)
            return

        parts = call.data.split(":")
        # ожидаем moder:<ok|rej>:<id>
        if len(parts) != 3:
            bot.answer_callback_query(call.id)
            return

        _, action, id_str = parts
        try:
            sugg_id = int(id_str)
        except ValueError:
            bot.answer_callback_query(call.id)
            return

        # Если нужно, защитимся от повторного решения
        if get_suggestion:
            try:
                s = get_suggestion(sugg_id)
                if s and s.get("status") in {"approved", "rejected"}:
                    bot.answer_callback_query(call.id, "Уже принято решение", show_alert=False)
                    return
            except Exception as e:
                print(f"[moderation] get_suggestion failed: {e}")

        # Применяем решение
        if action == "ok":
            set_status(sugg_id, "approved")
            # Меняем клавиатуру в карточке
            try:
                bot.edit_message_reply_markup(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    reply_markup=kb_moderation_final("✅ Одобрено")
                )
            except Exception as e:
                print(f"[moderation] edit_message_reply_markup(ok) failed: {e}")
            bot.answer_callback_query(call.id, "Одобрено", show_alert=False)

            # Опционально уведомим автора в ЛС
            if get_suggestion:
                try:
                    s = get_suggestion(sugg_id)
                    uid = s and s.get("user_id")
                    if uid:
                        bot.send_message(uid, f"✅ Ваша заявка #{sugg_id} одобрена.")
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
                        bot.send_message(uid, f"🚫 Ваша заявка #{sugg_id} отклонена.")
                except Exception as e:
                    print(f"[moderation] notify user(rej) failed: {e}")
        else:
            bot.answer_callback_query(call.id)
