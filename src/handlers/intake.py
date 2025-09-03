from telebot import types, apihelper
from ..config import Settings
from ..utils.text import sanitize_text, human_now
from ..keyboards.common import kb_moderation

PUBLIC_CHAT_ID = Settings.public_chat_id
MANAGERS_CHAT_ID = Settings.managers_chat_id

def register_handlers(bot):
    def is_command(m: types.Message) -> bool:
        t = (m.text or m.caption or "")
        return t.startswith("/")

    @bot.message_handler(
        content_types=['text', 'photo', 'document', 'video', 'voice'],
        func=lambda m: not is_command(m)  # ← команды игнорим (учитывая caption)
    )
    def intake(message: types.Message):
        if message.chat.type != "private":
            return
        try:
            member = bot.get_chat_member(PUBLIC_CHAT_ID, message.from_user.id)
            if member.status in ("left", "kicked"):
                bot.send_message(message.chat.id, "🛡️ Доступ только для участников общей группы. Вступите и напишите снова.")
                return
        except apihelper.ApiTelegramException as e:
            print(f"[get_chat_member] failed: {e}")
            bot.send_message(message.chat.id, "⚠️ Бот не видит общую группу или нет прав. Сообщите администратору.")
            return

        # текст берем из caption для медиа или из text
        text = sanitize_text(message.text or message.caption or "")
        reply = f"✅ Принято. Время: {human_now()}\nТекст: {text or '—'}"

        if message.photo:
            file_id = message.photo[-1].file_id
            bot.send_photo(message.chat.id, file_id, caption=reply, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, reply, parse_mode="HTML")

        # ---- карточка для менеджеров с кнопками ----
        header = f"<b>Новое предложение</b>\n⏱ {human_now()}"
        if not MANAGERS_CHAT_ID:
            # если не настроен — пропустим отправку менеджерам
            return

        if message.photo:
            file_id = message.photo[-1].file_id
            caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"
            bot.send_photo(
                chat_id=MANAGERS_CHAT_ID,
                photo=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb_moderation()
            )
        elif message.document:
            caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"
            bot.send_document(
                MANAGERS_CHAT_ID, message.document.file_id,
                caption=caption, parse_mode="HTML",
                reply_markup=kb_moderation()
            )
        elif message.video:
            caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"
            bot.send_video(
                MANAGERS_CHAT_ID, message.video.file_id,
                caption=caption, parse_mode="HTML",
                reply_markup=kb_moderation()
            )
        elif message.voice:
            # voice не поддерживает caption-клавиатуру в старых клиентах → отправим текст с кнопками рядом
            m = bot.send_message(
                MANAGERS_CHAT_ID,
                f"{header}\n\n<b>Голосовое сообщение</b>\n<b>Текст:</b> {text or '—'}",
                parse_mode="HTML",
                reply_markup=kb_moderation()
            )
            bot.send_voice(MANAGERS_CHAT_ID, message.voice.file_id)
        else:
            # чистый текст
            bot.send_message(
                MANAGERS_CHAT_ID,
                f"{header}\n\n<b>Текст:</b> {text or '—'}",
                parse_mode="HTML",
                reply_markup=kb_moderation()
            )