from telebot import types, apihelper
from ..config import Settings
from ..utils.text import sanitize_text, human_now
from ..keyboards.common import kb_moderation, criteria_keyboard
from .criteria import _STATE  # общее состояние диалога

PUBLIC_CHAT_ID = Settings.public_chat_id
MANAGERS_CHAT_ID = Settings.managers_chat_id

def _is_waiting_text(user_id: int) -> bool:
    return _STATE.get(user_id, {}).get("stage") == "await_text"

def _pop_category(user_id: int) -> str:
    data = _STATE.pop(user_id, {})  # сброс state
    return data.get("category", "—")

def register_handlers(bot):
    @bot.message_handler(
        content_types=["text", "photo", "document", "video", "voice"]
    )
    def intake(message: types.Message):
        if message.chat.type != "private":
            return

        # команды — не здесь
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
            bot.send_message(message.chat.id, "⚠️ Бот не видит общую группу или нет прав. Сообщите администратору.")
            return

        uid = message.from_user.id

        # 1) Если уже ждём текст после выбора категории — финализируем заявку
        if _is_waiting_text(uid):
            category = _pop_category(uid)
            _finalize_submission(bot, message, category)
            return

        # 2) Иначе — это первое сообщение без /suggest:
        #    сохраняем черновик и просим выбрать категорию
        draft_text = sanitize_text(message.text or message.caption or "")
        draft_media = None
        if message.photo:
            draft_media = {"type": "photo", "file_id": message.photo[-1].file_id}
        elif message.document:
            draft_media = {"type": "document", "file_id": message.document.file_id}
        elif message.video:
            draft_media = {"type": "video", "file_id": message.video.file_id}
        elif message.voice:
            draft_media = {"type": "voice", "file_id": message.voice.file_id}

        _STATE[uid] = {
            "stage": "await_category_from_text",
            "draft_text": draft_text,
            "draft_media": draft_media,
        }

        bot.send_message(
            message.chat.id,
            "Выберите категорию вашего предложения:",
            reply_markup=criteria_keyboard()
        )

def _finalize_submission(bot, message: types.Message, category: str):
    """Общая отправка подтверждения пользователю и карточки менеджерам."""
    text = sanitize_text(message.text or message.caption or "")
    ts = human_now()

    # подтверждение пользователю
    user_caption = f"✅ Принято. Время: {ts}\nКатегория: {category}\nТекст: {text or '—'}"
    if message.photo:
        bot.send_photo(message.chat.id, message.photo[-1].file_id, caption=user_caption, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, user_caption, parse_mode="HTML")

    # менеджерам
    if not MANAGERS_CHAT_ID:
        return

    header = f"<b>Новое предложение</b>\n⏱ {ts}\n<b>Категория:</b> {category}"
    managers_caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"

    if message.photo:
        bot.send_photo(
            chat_id=MANAGERS_CHAT_ID,
            photo=message.photo[-1].file_id,
            caption=managers_caption,
            parse_mode="HTML",
            reply_markup=kb_moderation()
        )
    elif message.document:
        bot.send_document(
            MANAGERS_CHAT_ID, message.document.file_id,
            caption=managers_caption, parse_mode="HTML",
            reply_markup=kb_moderation()
        )
    elif message.video:
        bot.send_video(
            MANAGERS_CHAT_ID, message.video.file_id,
            caption=managers_caption, parse_mode="HTML",
            reply_markup=kb_moderation()
        )
    elif message.voice:
        bot.send_message(
            MANAGERS_CHAT_ID,
            f"{header}\n\n<b>Голосовое сообщение</b>\n<b>Текст:</b> {text or '—'}",
            parse_mode="HTML",
            reply_markup=kb_moderation()
        )
        bot.send_voice(MANAGERS_CHAT_ID, message.voice.file_id)
    else:
        bot.send_message(
            MANAGERS_CHAT_ID,
            managers_caption,
            parse_mode="HTML",
            reply_markup=kb_moderation()
        )
