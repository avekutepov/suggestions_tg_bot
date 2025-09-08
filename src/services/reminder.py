import threading
import time
from datetime import datetime, timedelta
from telebot import types
from ..config import Settings

WEEKDAY_TUESDAY = 1  # Monday=0, Tuesday=1, ... Sunday=6

def _next_run(after: datetime, weekday: int, hour: int, minute: int) -> datetime:
    """Вернёт ближайшую дату-время запуска после 'after' (включая сегодня, если время ещё не прошло)."""
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
        "🔔 Напоминание: каждую **вторник** принимаем анонимные предложения.\n\n"
        "Отправьте идею боту командой /suggest или нажмите кнопку ниже."
    )
    kb = _build_dm_keyboard(bot)
    # В группе лучше без Markdown/HTML, чтобы не ловить ошибки форматирования
    bot.send_message(chat_id, text, reply_markup=kb, parse_mode=None, disable_notification=True)

def start_weekly_public_reminder(bot, weekday: int = WEEKDAY_TUESDAY, hour: int = 10, minute: int = 0):
    """
    Запускает фоновую задачу: каждую неделю в указанный день/время (локальное время процесса)
    отправляет напоминание в Settings.public_chat_id.
    По умолчанию — вторник 10:00.
    """
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
