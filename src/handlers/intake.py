from telebot import types, apihelper
from ..config import Settings
from ..utils.text import sanitize_text, human_now
from ..keyboards.common import kb_moderation, criteria_keyboard
from ..db import add_suggestion
from .criteria import _STATE  # общее состояние диалога

PUBLIC_CHAT_ID = Settings.public_chat_id
MANAGERS_CHAT_ID = Settings.managers_chat_id

def _is_waiting_text(user_id: int) -> bool:
    return _STATE.get(user_id, {}).get("stage") == "await_text"

def _pop_category(user_id: int) -> str:
    data = _STATE.pop(user_id, {})  # сброс state
    return data.get("category", "—")

def register_handlers(bot):
    @bot.message_handler(content_types=["text", "photo", "document", "video", "voice"])
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
                bot.send_message(message.chat.id, "🛡️ Доступ только для участников общей группы. Вступите и напишите снова.")
                return
        except apihelper.ApiTelegramException as e:
            print(f"[get_chat_member] failed: {e}")
            bot.send_message(message.chat.id, "⚠️ Бот не видит общую группу или нет прав. Сообщите администратору.")
            return

        uid = message.from_user.id

        # Если уже ждём текст после выбора категории — используем выбранную категорию
        if _is_waiting_text(uid):
            category = _pop_category(uid)
            _finalize_submission(bot, message, category)
            return

        # Иначе — первое сообщение без /suggest: спросим категорию и сохраним черновик
        draft_text = sanitize_text(message.text or message.caption or "")
        draft_media = None
        media_type = None
        media_file_id = None

        if message.photo:
            media_type = "photo"
            media_file_id = message.photo[-1].file_id
        elif message.document:
            media_type = "document"
            media_file_id = message.document.file_id
        elif message.video:
            media_type = "video"
            media_file_id = message.video.file_id
        elif message.voice:
            media_type = "voice"
            media_file_id = message.voice.file_id

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

def _finalize_submission(bot, message: types.Message, category: str):
    """Сохраняем заявку в БД, подтверждаем пользователю и шлём в чат менеджеров с кнопками."""
    text = sanitize_text(message.text or message.caption or "")
    ts = human_now()

    # Определяем медиа
    media_type = None
    media_file_id = None
    if message.photo:
        media_type, media_file_id = "photo", message.photo[-1].file_id
    elif message.document:
        media_type, media_file_id = "document", message.document.file_id
    elif message.video:
        media_type, media_file_id = "video", message.video.file_id
    elif message.voice:
        media_type, media_file_id = "voice", message.voice.file_id

    # Пишем в БД → получаем id
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

    # Подтверждение пользователю
    user_caption = f"✅ Принято. Время: {ts}\nКатегория: {category}\nНомер: #{sugg_id}\nТекст: {text or '—'}"
    if message.photo:
        bot.send_photo(message.chat.id, message.photo[-1].file_id, caption=user_caption, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, user_caption, parse_mode="HTML")

    # Менеджерам — карточка + кнопки модерации с id
    if not MANAGERS_CHAT_ID:
        return

    header = f"<b>Новое предложение</b> #{sugg_id}\n⏱ {ts}\n<b>Категория:</b> {category}"
    managers_caption = f"{header}\n\n<b>Текст:</b> {text or '—'}"

    if media_type == "photo":
        bot.send_photo(MANAGERS_CHAT_ID, media_file_id, caption=managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
    elif media_type == "document":
        bot.send_document(MANAGERS_CHAT_ID, media_file_id, caption=managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
    elif media_type == "video":
        bot.send_video(MANAGERS_CHAT_ID, media_file_id, caption=managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
    elif media_type == "voice":
        m = bot.send_message(MANAGERS_CHAT_ID, managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
        bot.send_voice(MANAGERS_CHAT_ID, media_file_id)
    else:
        bot.send_message(MANAGERS_CHAT_ID, managers_caption, parse_mode="HTML", reply_markup=kb_moderation(sugg_id))
