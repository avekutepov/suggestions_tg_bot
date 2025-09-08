from telebot import types
from html import escape
from ..db import add_suggestion
from ..config import Settings
from ..utils.text import sanitize_text, human_now
from ..keyboards.common import criteria_keyboard, kb_moderation
from .criteria import _STATE, _author_line

def _reset(uid: int):
    _STATE.pop(uid, None)

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.chat.type == 'private' and (m.text or '').strip() == "❌ Отмена")
    def on_cancel_reply(m: types.Message):
        _reset(m.from_user.id)
        bot.send_message(
            m.chat.id,
            "🚫 Действие отменено. Используйте /suggest, чтобы начать заново.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    @bot.message_handler(
        content_types=['text', 'photo', 'document', 'video', 'voice'],
        func=lambda m: m.chat.type == 'private' and not (m.text and m.text.startswith('/'))
    )
    def on_any_message(message: types.Message):

        uid = message.from_user.id
        st = _STATE.get(uid) or {}
        raw_text = message.text or message.caption or ""
        text = sanitize_text(raw_text)
        text_html = escape(text) if text else "—"

        draft_media = None
        if message.photo:
            draft_media = {"type": "photo", "file_id": message.photo[-1].file_id}
        elif message.document:
            draft_media = {"type": "document", "file_id": message.document.file_id}
        elif message.video:
            draft_media = {"type": "video", "file_id": message.video.file_id}
        elif message.voice:
            draft_media = {"type": "voice", "file_id": message.voice.file_id}

        # A) /suggest -> категория уже выбрана
        if st.get("stage") == "await_text":
            category = st.get("category") or "—"
            _reset(uid)

            sugg_id = add_suggestion(
                user_id=uid,
                text=text,
                category=category,
                media_type=(draft_media or {}).get("type"),
                media_file_id=(draft_media or {}).get("file_id"),
                user_username=message.from_user.username,
                user_first_name=message.from_user.first_name,
                user_last_name=message.from_user.last_name,
            )

            ts = human_now()
            user_caption = (
                f"✅ Принято. Время: {ts}\n"
                f"Категория: {escape(category)}\n"
                f"Номер: #{sugg_id}\n"
                f"Текст: {text_html}"
            )

            if draft_media and draft_media.get("type") == "photo":
                bot.send_photo(
                    message.chat.id,
                    draft_media["file_id"],
                    caption=user_caption,
                    parse_mode="HTML",
                    reply_markup=types.ReplyKeyboardRemove()
                )
            else:
                bot.send_message(
                    message.chat.id,
                    user_caption,
                    parse_mode="HTML",
                    reply_markup=types.ReplyKeyboardRemove()
                )

            man_id = Settings.managers_chat_id
            if man_id:
                header = (
                    f"<b>Новое предложение</b> #{sugg_id}\n"
                    f"⏱ {ts}\n"
                    f"<b>Категория:</b> {escape(category)}\n"
                    f"{_author_line(message.from_user)}"
                )
                caption = f"{header}\n\n<b>Текст:</b> {text_html}"
                if draft_media and draft_media.get("type") == "photo":
                    bot.send_photo(man_id, draft_media["file_id"], caption=caption, parse_mode="HTML",
                                   reply_markup=kb_moderation(sugg_id))
                else:
                    bot.send_message(man_id, caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
            return

        # B) ждём категорию (через /suggest) -> обновляем черновик
        if st.get("stage") == "await_category_from_text":
            st.update({
                "draft_text": text,
                "draft_media": draft_media,
            })
            _STATE[uid] = st
            return

        # C) пользователь начал с текста/медиа -> просим выбрать категорию
        _STATE[uid] = {
            "stage": "await_category_from_text",
            "category": None,
            "draft_text": text,
            "draft_media": draft_media,
        }
        bot.send_message(
            message.chat.id,
            "Выберите категорию вашего предложения:",
            reply_markup=criteria_keyboard()
        )
