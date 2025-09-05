from telebot import types
from ..db import add_suggestion
from ..utils.text import human_now, sanitize_text
from ..keyboards.common import kb_moderation
from ..config import Settings


def finalize_submission(bot, message: types.Message, category: str) -> int:
    """
    Пишем в БД → подтверждаем пользователю → шлём карточку менеджерам с кнопками.
    Возвращаем sugg_id.
    """
    text = sanitize_text(message.text or message.caption or "")
    ts = human_now()

    # медиа
    media_type, media_file_id = None, None
    if message.photo:
        media_type, media_file_id = "photo", message.photo[-1].file_id
    elif message.document:
        media_type, media_file_id = "document", message.document.file_id
    elif message.video:
        media_type, media_file_id = "video", message.video.file_id
    elif message.voice:
        media_type, media_file_id = "voice", message.voice.file_id

    # БД
    sugg_id = add_suggestion(
        user_id=message.from_user.id,
        text=text,
        category=category,
        media_type=media_type,
        media_file_id=media_file_id,
        user_username=message.from_user.username,
        user_first_name=message.from_user.first_name,
        user_last_name=message.from_user.last_name,
    )

    # пользователю
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

    # менеджерам
    man_id = Settings.managers_chat_id
    if man_id:
        uid = message.from_user.id
        first = (message.from_user.first_name or "").strip()
        last  = (message.from_user.last_name or "").strip()
        display_name = (f"{first} {last}".strip()) or "пользователь"
        author_link = f'<a href="tg://user?id={uid}">{display_name}</a>'
        username_part = f" (@{message.from_user.username})" if message.from_user.username else ""

        header = (
            f"<b>Новое предложение</b> #{sugg_id}\n"
            f"⏱ {ts}\n"
            f"<b>Категория:</b> {category}\n"
            f"<b>Автор:</b> {author_link}{username_part}"
        )
        managers_caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"

        if media_type == "photo":
            bot.send_photo(man_id, media_file_id, caption=managers_caption, parse_mode="HTML",
                           reply_markup=kb_moderation(sugg_id))
        elif media_type == "document":
            bot.send_document(man_id, media_file_id, caption=managers_caption, parse_mode="HTML",
                              reply_markup=kb_moderation(sugg_id))
        elif media_type == "video":
            bot.send_video(man_id, media_file_id, caption=managers_caption, parse_mode="HTML",
                           reply_markup=kb_moderation(sugg_id))
        elif media_type == "voice":
            bot.send_message(man_id, managers_caption, parse_mode="HTML",
                             reply_markup=kb_moderation(sugg_id))
            bot.send_voice(man_id, media_file_id)
        else:
            bot.send_message(man_id, managers_caption, parse_mode="HTML",
                             reply_markup=kb_moderation(sugg_id))

    return sugg_id
