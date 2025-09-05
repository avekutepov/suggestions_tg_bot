from telebot import types
from ..keyboards.common import criteria_keyboard, cancel_reply_kb, kb_moderation
from ..utils.text import human_now
from ..config import Settings
from ..db import add_suggestion

# Простое состояние на пользователя:
# _STATE[user_id] = {
#   "stage": "await_text" | "await_category_from_text",
#   "category": str | None,
#   "draft_text": str | None,
#   "draft_media": {"type": "...", "file_id": "..."} | None
# }
_STATE = {}


def _reset(uid: int):
    _STATE.pop(uid, None)


def _author_line(u: types.User) -> str:
    first = (u.first_name or "").strip()
    last = (u.last_name or "").strip()
    name = (f"{first} {last}".strip()) or "пользователь"
    link = f'<a href="tg://user?id={u.id}">{name}</a>'
    uname = f" (@{u.username})" if u.username else ""
    return f"<b>Автор:</b> {link}{uname}"


def register_handlers(bot):
    @bot.message_handler(commands=["suggest", "idea", "criteria"])
    def start_flow(message: types.Message):
        # Запуск выбора категории «с нуля»
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
            bot.send_message(call.message.chat.id, "🚫 Действие отменено. Начните заново командой /suggest.")
            return

        mapping = {
            "crit_money": "💰 Экономия средств",
            "crit_time": "⏱ Экономия времени",
            "crit_process": "⚙ Улучшение процесса",
            "crit_safety": "🛡 Безопасность",
            "crit_other": "➕ Другое",
        }
        category = mapping.get(call.data, "—")

        st = _STATE.get(uid) or {}

        # СЦЕНАРИЙ B: пользователь сначала прислал сообщение (черновик),
        # теперь выбрал категорию → сразу оформляем
        if st.get("stage") == "await_category_from_text":
            draft_text = (st.get("draft_text") or "").strip()
            draft_media = st.get("draft_media")  # {"type": "...", "file_id": "..."} | None
            _reset(uid)

            sugg_id = add_suggestion(
                user_id=uid,
                text=draft_text,
                category=category,
                media_type=(draft_media or {}).get("type"),
                media_file_id=(draft_media or {}).get("file_id"),
                user_username=call.from_user.username,
                user_first_name=call.from_user.first_name,
                user_last_name=call.from_user.last_name,
            )

            ts = human_now()
            user_caption = (
                f"✅ Принято. Время: {ts}\n"
                f"Категория: {category}\n"
                f"Номер: #{sugg_id}\n"
                f"Текст: {draft_text or '—'}"
            )

            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id)

            if draft_media and draft_media.get("type") == "photo":
                bot.send_photo(call.message.chat.id, draft_media["file_id"], caption=user_caption, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, user_caption, parse_mode="HTML")

            man_id = Settings.managers_chat_id
            if man_id:
                header = (
                    f"<b>Новое предложение</b> #{sugg_id}\n"
                    f"⏱ {ts}\n"
                    f"<b>Категория:</b> {category}\n"
                    f"{_author_line(call.from_user)}"
                )
                managers_caption = f"{header}\n\n<b>Текст:</b> {draft_text or '—'}"
                dm = draft_media
                if dm and dm.get("type") == "photo":
                    bot.send_photo(man_id, dm["file_id"], caption=managers_caption, parse_mode="HTML",
                                   reply_markup=kb_moderation(sugg_id))
                elif dm and dm.get("type") == "document":
                    bot.send_document(man_id, dm["file_id"], caption=managers_caption, parse_mode="HTML",
                                      reply_markup=kb_moderation(sugg_id))
                elif dm and dm.get("type") == "video":
                    bot.send_video(man_id, dm["file_id"], caption=managers_caption, parse_mode="HTML",
                                   reply_markup=kb_moderation(sugg_id))
                elif dm and dm.get("type") == "voice":
                    bot.send_message(man_id, managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
                    bot.send_voice(man_id, dm["file_id"])
                else:
                    bot.send_message(man_id, managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
            return

        # СЦЕНАРИЙ A: обычный — выбрали категорию, дальше ждём текст
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
        category = (st.get("category") or "—").strip()
        text = (message.text or "").strip()
        ts = human_now()

        sugg_id = add_suggestion(
            user_id=message.from_user.id,
            text=text,
            category=category,
            media_type=None,
            media_file_id=None,
            user_username=message.from_user.username,
            user_first_name=message.from_user.first_name,
            user_last_name=message.from_user.last_name,
        )

        bot.send_message(
            message.chat.id,
            f"✅ Принято.\n<b>Категория:</b> {category}\n<b>Номер:</b> #{sugg_id}\n<b>Текст:</b> {text or '—'}",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )

        man_id = Settings.managers_chat_id
        if man_id:
            header = (
                f"<b>Новое предложение</b> #{sugg_id}\n"
                f"⏱ {ts}\n"
                f"<b>Категория:</b> {category}\n"
                f"{_author_line(message.from_user)}"
            )
            managers_caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"
            bot.send_message(man_id, managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
