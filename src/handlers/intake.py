from telebot import types, apihelper

from ..config import Settings
from ..utils.text import sanitize_text, human_now
from ..keyboards.common import criteria_keyboard, kb_moderation
from ..db import add_suggestion

# Берём общее состояние диалога и форматтер автора из criteria
from .criteria import _STATE, _author_line

PUBLIC_CHAT_ID = Settings.public_chat_id
MANAGERS_CHAT_ID = Settings.managers_chat_id


def _is_waiting_text(user_id: int) -> bool:
    return _STATE.get(user_id, {}).get("stage") == "await_text"


def _pop_category(user_id: int) -> str:
    # забираем и одновременно сбрасываем stage «await_text»
    data = _STATE.pop(user_id, {})
    return (data.get("category") or "—").strip()


def register_handlers(bot):
    @bot.message_handler(content_types=["text", "photo", "document", "video", "voice"])
    def intake(message: types.Message):
        """
        1) Если в ЛС пришла команда — пропускаем (это не сюда).
        2) Если ранее выбрали категорию и ждём текст → сразу оформляем предложение.
        3) Иначе это «черновик»: сохраняем text/media и просим выбрать категорию.
        """
        # работаем только в приватном чате
        if message.chat.type != "private":
            return

        # команды — не тут
        t_all = (message.text or message.caption or "")
        if t_all.startswith("/"):
            return

        # доступ только участникам общей группы
        try:
            member = bot.get_chat_member(PUBLIC_CHAT_ID, message.from_user.id)
            if member.status in ("left", "kicked"):
                bot.send_message(
                    message.chat.id,
                    "🛡️ Доступ только для участников общей группы. Вступите и напишите снова."
                )
                return
        except apihelper.ApiTelegramException as e:
            print(f"[get_chat_member] failed: {e}")
            bot.send_message(
                message.chat.id,
                "⚠️ Бот не видит общую группу или нет прав. Сообщите администратору."
            )
            return

        uid = message.from_user.id

        # === СЦЕНАРИЙ A: категория уже выбрана, ждём текст/медиа ===
        if _is_waiting_text(uid):
            category = _pop_category(uid)

            text = sanitize_text(message.text or message.caption or "")
            ts = human_now()

            # медиа (если есть)
            media_type, media_file_id = None, None
            if message.photo:
                media_type, media_file_id = "photo", message.photo[-1].file_id
            elif message.document:
                media_type, media_file_id = "document", message.document.file_id
            elif message.video:
                media_type, media_file_id = "video", message.video.file_id
            elif message.voice:
                media_type, media_file_id = "voice", message.voice.file_id

            # сохраняем
            sugg_id = add_suggestion(
                user_id=uid,
                text=text,
                category=category,
                media_type=media_type,
                media_file_id=media_file_id,
                user_username=message.from_user.username,
                user_first_name=message.from_user.first_name,
                user_last_name=message.from_user.last_name,
            )

            # подтверждение пользователю
            user_caption = (
                f"✅ Принято. Время: {ts}\n"
                f"Категория: {category}\n"
                f"Номер: #{sugg_id}\n"
                f"Текст: {text or '—'}"
            )
            if media_type == "photo":
                bot.send_photo(message.chat.id, media_file_id, caption=user_caption, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, user_caption, parse_mode="HTML")

            # менеджерам — карточка
            if MANAGERS_CHAT_ID:
                header = (
                    f"<b>Новое предложение</b> #{sugg_id}\n"
                    f"⏱ {ts}\n"
                    f"<b>Категория:</b> {category}\n"
                    f"{_author_line(message.from_user)}"
                )
                managers_caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"

                if media_type == "photo":
                    bot.send_photo(MANAGERS_CHAT_ID, media_file_id, caption=managers_caption,
                                   parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
                elif media_type == "document":
                    bot.send_document(MANAGERS_CHAT_ID, media_file_id, caption=managers_caption,
                                      parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
                elif media_type == "video":
                    bot.send_video(MANAGERS_CHAT_ID, media_file_id, caption=managers_caption,
                                   parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
                elif media_type == "voice":
                    bot.send_message(MANAGERS_CHAT_ID, managers_caption,
                                     parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
                    bot.send_voice(MANAGERS_CHAT_ID, media_file_id)
                else:
                    bot.send_message(MANAGERS_CHAT_ID, managers_caption,
                                     parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
            return

        # === СЦЕНАРИЙ B: это «черновик» — сначала пришёл текст/медиа, категории ещё нет ===
        draft_text = sanitize_text(message.text or message.caption or "")

        media_type, media_file_id = None, None
        if message.photo:
            media_type, media_file_id = "photo", message.photo[-1].file_id
        elif message.document:
            media_type, media_file_id = "document", message.document.file_id
        elif message.video:
            media_type, media_file_id = "video", message.video.file_id
        elif message.voice:
            media_type, media_file_id = "voice", message.voice.file_id

        # сохраняем черновик в состоянии и просим выбрать категорию
        _STATE[uid] = {
            "stage": "await_category_from_text",
            "draft_text": draft_text,
            "draft_media": {"type": media_type, "file_id": media_file_id} if media_type else None,
        }

        bot.send_message(
            message.chat.id,
            "Выберите категорию вашего предложения:",
            reply_markup=criteria_keyboard()
        )
