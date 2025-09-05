from telebot import types
from ..keyboards.common import criteria_keyboard, cancel_reply_kb
from ..utils.text import human_now
from ..services.flow_state import (
    reset, set_await_text, set_await_category_from_text,
    stage, pop_draft, pop_category
)
from ..services.submission import finalize_submission


def register_handlers(bot):
    @bot.message_handler(commands=["suggest", "idea", "criteria"])
    def start_flow(message: types.Message):
        reset(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "Выберите категорию вашего предложения:",
            reply_markup=criteria_keyboard()
        )

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("crit_"))
    def on_category(call: types.CallbackQuery):
        uid = call.from_user.id

        if call.data == "crit_cancel":
            reset(uid)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Выбор отменён ❌", show_alert=False)
            bot.send_message(call.message.chat.id, "🚫 Действие отменено. Начните заново командой /suggest.")
            return

        mapping = {
            "crit_money":   "💰 Экономия средств",
            "crit_time":    "⏱ Экономия времени",
            "crit_process": "⚙ Улучшение процесса",
            "crit_safety":  "🛡 Безопасность",
            "crit_other":   "➕ Другое",
        }
        category = mapping.get(call.data, "—")

        # Если уже есть черновик (первым шёл текст), завершаем сразу
        if stage(uid) == "await_category_from_text":
            draft = pop_draft(uid)  # {"draft_text": str, "draft_media": {...}|None}
            # Подменяем message полями черновика (текст/медиа) для единообразия
            class _Stub:  # минимальный объект с нужными атрибутами
                pass
            stub = _Stub()
            stub.chat = call.message.chat
            stub.from_user = call.from_user
            stub.text = draft["draft_text"]
            stub.caption = draft["draft_text"]
            dm = draft["draft_media"] or {}
            stub.photo = [types.PhotoSize(file_id=dm.get("file_id"))] if dm.get("type") == "photo" else None
            stub.document = types.Document(file_id=dm.get("file_id")) if dm.get("type") == "document" else None
            stub.video = types.Video(file_id=dm.get("file_id")) if dm.get("type") == "video" else None
            stub.voice = types.Voice(file_id=dm.get("file_id")) if dm.get("type") == "voice" else None

            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            bot.answer_callback_query(call.id)
            finalize_submission(bot=bot, message=stub, category=category)
            return

        # Иначе — обычный сценарий: выбрана категория, ждём текст
        set_await_text(uid, category)
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
        reset(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "🚫 Действие отменено. Чтобы начать заново — /suggest.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    @bot.message_handler(func=lambda m: stage(m.from_user.id) == "await_text", content_types=['text'])
    def got_text(message: types.Message):
        # Был выбран критерий, теперь пришёл текст — финализируем
        category = pop_category(message.from_user.id) or "—"
        finalize_submission(bot=bot, message=message, category=category)
