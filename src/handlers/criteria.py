# src/handlers/criteria.py
from telebot import types
from html import escape
from enum import Enum

from ..config import Settings
from ..db import add_suggestion
from ..utils.text import human_now
from ..keyboards.common import criteria_keyboard, kb_moderation, cancel_reply_kb
from ..utils.auth import is_allowed_user
from ..utils.media import send_media_with_caption


class SuggestStage(Enum):
    AWAIT_CATEGORY_FROM_TEXT = "await_category_from_text"  # сначала пришёл текст/медиа → ждём категорию
    AWAIT_TEXT = "await_text"                              # сначала выбрали категорию → ждём текст/медиа


_STATE: dict[int, dict] = {}


def _reset(uid: int):
    _STATE.pop(uid, None)


def _author_line(u: types.User) -> str:
    first = escape((u.first_name or "").strip())
    last  = escape((u.last_name  or "").strip())
    name = (f"{first} {last}".strip()) or "пользователь"
    link = f'<a href="tg://user?id={u.id}">{name}</a>'
    username_part = f" (@{escape(u.username)})" if u.username else ""
    return f"<b>Автор:</b> {link}{username_part}"


def register_handlers(bot):
    @bot.message_handler(commands=["suggest", "idea", "criteria"])
    def start_flow(message: types.Message):
        # работаем только в ЛС
        if message.chat.type != 'private':
            return

        # доступ только сотрудникам (участники public/managers)
        if not is_allowed_user(
            bot,
            message.from_user.id,
            allowed_chats=(Settings.public_chat_id, Settings.managers_chat_id),
        ):
            _reset(message.from_user.id)
            bot.send_message(
                message.chat.id,
                "⛔ Бот принимает предложения только от сотрудников. "
                "Убедитесь, что вы состоите в рабочей группе.",
            )
            return

        _STATE[message.from_user.id] = {
            "stage": SuggestStage.AWAIT_CATEGORY_FROM_TEXT.value,
            "category": None,
            "draft_text": None,
            "draft_media": None,
        }
        send_category_choice(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("crit_"))
    def on_category(call: types.CallbackQuery):
        uid = call.from_user.id

        # защита на коллбэках (клавиатура могла быть переслана)
        if not is_allowed_user(
            bot,
            uid,
            allowed_chats=(Settings.public_chat_id, Settings.managers_chat_id),
        ):
            try:
                bot.answer_callback_query(call.id, "Нет доступа", show_alert=False)
            except Exception:
                pass
            return

        if call.data == "crit_cancel":
            _reset(uid)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Выбор отменён ❌", show_alert=False)
            bot.send_message(
                call.message.chat.id,
                "🚫 Действие отменено. Начните заново командой /suggest.",
                reply_markup=types.ReplyKeyboardRemove()
            )
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

        # Сценарий: сначала текст/медиа, потом выбрали категорию → финализируем сразу
        if st.get("stage") == SuggestStage.AWAIT_CATEGORY_FROM_TEXT.value and (st.get("draft_text") or st.get("draft_media")):
            draft_text  = (st.get("draft_text") or "").strip()
            draft_media = st.get("draft_media")
            _reset(uid)

            if call.from_user and call.from_user.is_bot:
                bot.answer_callback_query(call.id)
                return

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
                f"Категория: {escape(category)}\n"
                f"Номер: #{sugg_id}\n"
                f"Текст: {escape(draft_text) if draft_text else '—'}"
            )

            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id)

            # пользователю — с медиа (любого типа)
            send_media_with_caption(
                bot, call.message.chat.id, draft_media, user_caption,
                reply_markup=types.ReplyKeyboardRemove()
            )

            # менеджерам
            man_id = Settings.managers_chat_id
            if man_id:
                header = (
                    f"<b>Новое предложение</b> #{sugg_id}\n"
                    f"⏱ {ts}\n"
                    f"<b>Категория:</b> {escape(category)}\n"
                    f"{_author_line(call.from_user)}"
                )
                caption = f"{header}\n\n<b>Текст:</b> {escape(draft_text) if draft_text else '—'}"
                send_media_with_caption(
                    bot, man_id, draft_media, caption,
                    reply_markup=kb_moderation(sugg_id)
                )
            return

        # Сценарий: выбрали категорию — ждём текст/медиа
        _STATE[uid] = {
            "stage": SuggestStage.AWAIT_TEXT.value,
            "category": category,
            "draft_text": None,
            "draft_media": None,
        }
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
        bot.answer_callback_query(call.id)
        send_text_prompt(bot, call.message.chat.id, category)


# --- вспомогательные отправки ---
def send_category_choice(bot, chat_id: int):
    bot.send_message(
        chat_id,
        "Выберите категорию вашего предложения:",
        reply_markup=criteria_keyboard()
    )


def send_text_prompt(bot, chat_id: int, category: str):
    bot.send_message(
        chat_id,
        f"Категория «{escape(category)}» выбрана.\nТеперь отправьте текст предложения или прикрепите фото/документ.",
        parse_mode="HTML",
        reply_markup=cancel_reply_kb()
    )
