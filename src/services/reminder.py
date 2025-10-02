import threading
import time
from datetime import datetime, timedelta
from telebot import types
from ..config import Settings

WEEKDAY_TUESDAY = 1  # Вторник

def _next_run(after: datetime, weekday: int, hour: int, minute: int) -> datetime:
    target = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # прокрутка до нужного дня недели
    days_ahead = (weekday - target.weekday()) % 7
    target = target + timedelta(days=days_ahead)
    # если время уже прошло сегодня — перенос на следующую неделю
    if target <= after:
        target = target + timedelta(days=7)
    return target

def _build_dm_keyboard(bot) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    try:
        me = bot.get_me()
        if me and me.username:
            kb.add(types.InlineKeyboardButton("✍️ Написать предложение", url=f"https://t.me/{me.username}?start=suggest"))
    except Exception:
        pass
    return kb

def _send_reminder(bot):
    chat_id = Settings.public_chat_id
    if not chat_id:
        return
    text = (
        "👋 Коллеги, у нас есть бот(t.me/aprofilkz_bot) для предложений и идей.\n\n"
        "📌 Как отправить предложение:\n"
        "1️⃣ Нажмите на команду suggest или напишите боту команду /suggest, либо нажмите кнопку «Написать предложение»\n"
        "2️⃣ Выберите категорию (💰 Экономия средств, ⏱ Экономия времени, ⚙ Улучшение процессов, 🛡 Безопасность и др.)\n"
        "3️⃣ Напишите предложение (можно прикрепить фото или видео).\n\n"
        "✅ Все предложения будут рассмотрены руководством.\n"
        "💵 Идеи, которые реально приведут к улучшениям, будут <b>поощрены</b>.\n\n"
        "Бот доступен только участникам этой группы, поэтому ваши идеи остаются внутри компании.\n"
        "Бот <b>анонимный</b>, не стесняйтесь предлагать — даже небольшие <b>улучшения</b> очень важны для компании!"
    )
    kb = _build_dm_keyboard(bot)
    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML", disable_notification=True)

def start_weekly_public_reminder(bot, weekday: int = WEEKDAY_TUESDAY, hour: int = 10, minute: int = 0):
    def worker():
        while True:
            now = datetime.now()
            run_at = _next_run(now, weekday=weekday, hour=hour, minute=minute)
            sleep_s = (run_at - now).total_seconds()
            if sleep_s < 0:
                sleep_s = 60
            time.sleep(sleep_s)
            try:
                _send_reminder(bot)
            except Exception:
                pass
            try:
                pass
            except Exception:
                pass

    t = threading.Thread(target=worker, name="weekly_public_reminder", daemon=True)
    t.start()
    return t

def register_handlers(bot):
    @bot.message_handler(commands=["remind"])
    def manual_reminder(message: types.Message):
        if message.chat.id != Settings.managers_chat_id:
            return
        _send_reminder(bot)
        bot.reply_to(message, "✅ Напоминание отправлено в общую группу")
