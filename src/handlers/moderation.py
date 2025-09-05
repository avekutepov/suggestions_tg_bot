# src/handlers/moderation.py
from telebot import types
from ..config import Settings
from ..db import update_status, get_suggestion
from ..utils.text import human_now

PUBLIC_CHAT_ID = Settings.public_chat_id

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("moder:"))
    def on_moder(call: types.CallbackQuery):
        # data: moder:approve:123  | moder:reject:123
        try:
            _, action, raw_id = call.data.split(":", 2)
            sugg_id = int(raw_id)
        except Exception:
            bot.answer_callback_query(call.id, "Некорректные данные.", show_alert=True)
            return

        sugg = get_suggestion(sugg_id)
        if not sugg:
            _safe_rm_kb(bot, call)
            bot.answer_callback_query(call.id, "Заявка не найдена.", show_alert=True)
            return

        ts = human_now()
        category = sugg.get("category") or "—"
        base = f"#{sugg_id}\n⏱ {ts}\n<b>Категория:</b> {category}\n\n<b>Текст:</b> {sugg.get('text') or '—'}"

        if action == "approve":
            update_status(sugg_id, "approved")
            _publish_to_public(bot, sugg)  # отправим в общий чат
            # обновим карточку у менеджеров
            new_text = f"✅ <b>Одобрено</b> {base}"
            _edit_manager_message(bot, call, new_text)
            bot.answer_callback_query(call.id, "Одобрено ✅")
        elif action == "reject":
            update_status(sugg_id, "rejected")
            new_text = f"🚫 <b>Отклонено</b> {base}"
            _edit_manager_message(bot, call, new_text)
            bot.answer_callback_query(call.id, "Отклонено 🚫")
        else:
            bot.answer_callback_query(call.id, "Неизвестное действие.", show_alert=True)

def _publish_to_public(bot, sugg: dict):
    """Публикация одобренной заявки в общий чат."""
    if not PUBLIC_CHAT_ID:
        return
    caption = (
        f"✅ <b>Одобрено</b> #{sugg['id']}\n"
        f"<b>Категория:</b> {sugg.get('category') or '—'}\n\n"
        f"<b>Текст:</b> {sugg.get('text') or '—'}"
    )
    mtype = sugg.get("media_type")
    fid = sugg.get("media_file_id")

    try:
        if mtype == "photo" and fid:
            bot.send_photo(PUBLIC_CHAT_ID, fid, caption=caption, parse_mode="HTML")
        elif mtype == "document" and fid:
            bot.send_document(PUBLIC_CHAT_ID, fid, caption=caption, parse_mode="HTML")
        elif mtype == "video" and fid:
            bot.send_video(PUBLIC_CHAT_ID, fid, caption=caption, parse_mode="HTML")
        elif mtype == "voice" and fid:
            # у voice может не быть caption — отправим подпись отдельным сообщением
            bot.send_message(PUBLIC_CHAT_ID, caption, parse_mode="HTML")
            bot.send_voice(PUBLIC_CHAT_ID, fid)
        else:
            bot.send_message(PUBLIC_CHAT_ID, caption, parse_mode="HTML")
    except Exception as e:
        # Не падаем, просто лог
        print(f"[publish_to_public] error: {e}")

def _edit_manager_message(bot, call: types.CallbackQuery, new_text: str):
    """
    Пытаемся обновить исходную карточку у менеджеров:
    - если это было медиа → edit_message_caption(reply_markup=None)
    - если это было текстовое сообщение → edit_message_text(reply_markup=None)
    Если редактировать нельзя — снимаем клавиатуру и отправляем отдельное сервисное сообщение.
    """
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # 1) снять клавиатуру в любом случае, чтобы нельзя было нажимать повторно
    #   (если удастся отредактировать текст/подпись — клавиатура снимется там)
    try:
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
    except Exception:
        pass

    # 2) попытка редактировать подпись у медиа
    try:
        if getattr(call.message, "content_type", None) in ("photo", "video", "document", "audio"):
            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=msg_id,
                caption=new_text,
                parse_mode="HTML",
                reply_markup=None
            )
            return
    except Exception:
        # продолжим пытаться как текст
        pass

    # 3) попытка редактировать текст
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=new_text,
            parse_mode="HTML",
            reply_markup=None
        )
        return
    except Exception:
        # 4) если не получилось — отправим отдельное сервисное сообщение (reply)
        try:
            bot.send_message(
                chat_id,
                new_text,
                parse_mode="HTML",
                reply_to_message_id=msg_id
            )
        except Exception as e:
            print(f"[edit_manager_message] fallback send_message error: {e}")

def _safe_rm_kb(bot, call: types.CallbackQuery):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
