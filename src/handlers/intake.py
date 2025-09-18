from telebot import types
from html import escape

from ..db import add_suggestion
from ..config import Settings
from ..utils.text import sanitize_text, human_now
from ..keyboards.common import criteria_keyboard, kb_moderation
from .criteria import _STATE, _author_line
from ..utils.auth import is_allowed_user
from ..utils.media import send_media_with_caption


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
        if message.from_user and message.from_user.is_bot:
            return

        if not is_allowed_user(
            bot, message.from_user.id,
            allowed_chats=(Settings.public_chat_id, Settings.managers_chat_id)
        ):
            bot.send_message(
                message.chat.id,
                "❌ Бот принимает предложения только от сотрудников. "
                "Если вы сотрудник — убедитесь, что состоите в рабочей группе."
            )
            return

        uid = message.from_user.id
        st = _STATE.get(uid) or {}

        raw_text = message.text or message.caption or ""
        text = sanitize_text(raw_text)
        text_html = escape(text) if text else "—"

        # Собираем медиу, если есть
        draft_media = None
        if message.photo:
            draft_media = {"type": "photo", "file_id": message.photo[-1].file_id}
        elif message.document:
            draft_media = {"type": "document", "file_id": message.document.file_id}
        elif message.video:
            draft_media = {"type": "video", "file_id": message.video.file_id}
        elif message.voice:
            draft_media = {"type": "voice", "file_id": message.voice.file_id}

        # A) /suggest -> категория уже выбрана: сразу сохраняем
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

            # Пользователю
            send_media_with_caption(
                bot, message.chat.id, draft_media, user_caption,
                reply_markup=types.ReplyKeyboardRemove()
            )

            # Менеджерам
            man_id = Settings.managers_chat_id
            if man_id:
                header = (
                    f"<b>Новое предложение</b> #{sugg_id}\n"
                    f"⏱ {ts}\n"
                    f"<b>Категория:</b> {escape(category)}\n"
                    f"{_author_line(message.from_user)}"
                )
                caption = f"{header}\n\n<b>Текст:</b> {text_html}"
                send_media_with_caption(
                    bot, man_id, draft_media, caption,
                    reply_markup=kb_moderation(sugg_id)
                )
            return

        # B) ждём категорию (после /suggest): обновляем черновик и ждём выбора
        if st.get("stage") == "await_category_from_text":
            st.update({
                "draft_text": text,
                "draft_media": draft_media,
            })
            _STATE[uid] = st
            return

        # C) пользователь начал с текста/медиа: просим выбрать категорию
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
