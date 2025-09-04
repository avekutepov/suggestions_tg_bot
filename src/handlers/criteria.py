from telebot import types
from ..keyboards.common import criteria_keyboard, cancel_reply_kb
from ..config import Settings
from ..utils.text import human_now
from ..keyboards.common import kb_moderation

_STATE = {}  

def _reset(uid: int):
    _STATE.pop(uid, None)

def register_handlers(bot):
    @bot.message_handler(commands=["suggest", "idea", "criteria"])
    def start_flow(message: types.Message):
        _reset(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Выберите категорию вашего предложения:",
            reply_markup=criteria_keyboard()
        )

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("crit_"))
    def on_category(call: types.CallbackQuery):
        uid = call.from_user.id

        if call.data == "crit_cancel":
            _reset(uid)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Выбор отменён ❌", show_alert=False)
            bot.send_message(call.message.chat.id, "🚫 Отменено. Начните заново командой /suggest.")
            return

        mapping = {
            "crit_money":   "💰 Экономия средств",
            "crit_time":    "⏱ Экономия времени",
            "crit_process": "⚙ Улучшение процесса",
            "crit_safety":  "🛡 Безопасность",
            "crit_other":   "➕ Другое",
        }
        category = mapping.get(call.data, "—")

        st = _STATE.get(uid) or {}

        # Если до выбора категории пользователь уже прислал сообщение — финализируем сразу
        if st.get("stage") == "await_category_from_text":
            draft_text = st.get("draft_text") or ""
            draft_media = st.get("draft_media")
            _reset(uid)

            ts = human_now()
            user_caption = f"✅ Принято. Время: {ts}\nКатегория: {category}\nТекст: {draft_text or '—'}"

            # подтверждение пользователю
            if draft_media and draft_media.get("type") == "photo":
                bot.send_photo(call.message.chat.id, draft_media["file_id"], caption=user_caption, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, user_caption, parse_mode="HTML")

            # менеджерам
            man_id = Settings.managers_chat_id
            if man_id:
                header = f"<b>Новое предложение</b>\n⏱ {ts}\n<b>Категория:</b> {category}"
                managers_caption = f"{header}\n\n<b>Текст:</b> {draft_text or '—'}"

                if draft_media:
                    t = draft_media.get("type")
                    fid = draft_media.get("file_id")
                    if t == "photo":
                        bot.send_photo(man_id, fid, caption=managers_caption, parse_mode="HTML", reply_markup=kb_moderation())
                    elif t == "document":
                        bot.send_document(man_id, fid, caption=managers_caption, parse_mode="HTML", reply_markup=kb_moderation())
                    elif t == "video":
                        bot.send_video(man_id, fid, caption=managers_caption, parse_mode="HTML", reply_markup=kb_moderation())
                    elif t == "voice":
                        bot.send_message(man_id, managers_caption, parse_mode="HTML", reply_markup=kb_moderation())
                        bot.send_voice(man_id, fid)
                else:
                    bot.send_message(man_id, managers_caption, parse_mode="HTML", reply_markup=kb_moderation())

            # снимаем inline-кнопки под исходным сообщением с категориями
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass

            bot.answer_callback_query(call.id)
            return

        # Обычный сценарий: выбрали категорию → ждём текст
        _STATE[uid] = {"stage": "await_text", "category": category}
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass

        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            f"✅ Категория: <b>{category}</b>\nНапишите ваше предложение (или нажмите «❌ Отмена»).",
            parse_mode="HTML",
            reply_markup=cancel_reply_kb()
        )

    @bot.message_handler(func=lambda m: (m.text or "").strip().lower() in {"❌ отмена", "/cancel"})
    def cancel_anywhere(message: types.Message):
        _reset(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "🚫 Действие отменено. Чтобы начать заново — /suggest.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    @bot.message_handler(func=lambda m: _STATE.get(m.from_user.id, {}).get("stage") == "await_text",
                         content_types=['text'])
    def got_text(message: types.Message):
        st = _STATE.pop(message.from_user.id, {})
        category = st.get("category", "—")
        text = (message.text or "").strip()

        bot.send_message(
            message.chat.id,
            f"✅ Принято.\n<b>Категория:</b> {category}\n<b>Текст:</b> {text}",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )

        man_id = Settings.managers_chat_id
        if man_id:
            ts = human_now()
            header = f"<b>Новое предложение</b>\n⏱ {ts}\n<b>Категория:</b> {category}"
            managers_caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"
            bot.send_message(man_id, managers_caption, parse_mode="HTML", reply_markup=kb_moderation())
