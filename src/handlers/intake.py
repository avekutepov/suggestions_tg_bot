from telebot import types, apihelper
from ..config import Settings
from ..utils.text import sanitize_text
from ..keyboards.common import criteria_keyboard
from ..services.flow_state import (
    stage, pop_category, set_await_category_from_text
)
from ..services.submission import finalize_submission

PUBLIC_CHAT_ID = Settings.public_chat_id


def register_handlers(bot):
    @bot.message_handler(content_types=["text", "photo", "document", "video", "voice"])
    def intake(message: types.Message):
        if message.chat.type != "private":
            return

        # команды обрабатывают другие хендлеры
        t_all = (message.text or message.caption or "")
        if t_all.startswith("/"):
            return

        # доступ только участникам общей группы
        try:
            member = bot.get_chat_member(PUBLIC_CHAT_ID, message.from_user.id)
            if member.status in ("left", "kicked"):
                bot.send_message(message.chat.id, "🛡️ Доступ только для участников общей группы. Вступите и напишите снова.")
                return
        except apihelper.ApiTelegramException:
            bot.send_message(message.chat.id, "⚠️ Бот не видит общую группу или нет прав. Сообщите администратору.")
            return

        uid = message.from_user.id

        # Если до этого была выбрана категория и ждём текст — финализируем
        if stage(uid) == "await_text":
            category = pop_category(uid) or "—"
            finalize_submission(bot=bot, message=message, category=category)
            return

        # Иначе это первое сообщение без /suggest → сохраняем черновик и спрашиваем категорию
        draft_text = sanitize_text(message.text or message.caption or "")
        dm_type, dm_file_id = None, None
        if message.photo:
            dm_type, dm_file_id = "photo", message.photo[-1].file_id
        elif message.document:
            dm_type, dm_file_id = "document", message.document.file_id
        elif message.video:
            dm_type, dm_file_id = "video", message.video.file_id
        elif message.voice:
            dm_type, dm_file_id = "voice", message.voice.file_id

        set_await_category_from_text(uid,
                                     draft_text=draft_text,
                                     draft_media={"type": dm_type, "file_id": dm_file_id} if dm_type else None)

        bot.send_message(
            message.chat.id,
            "Выберите категорию вашего предложения:",
            reply_markup=criteria_keyboard()
        )
