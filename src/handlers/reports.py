from telebot import types
from html import escape
from datetime import datetime, timedelta

from ..db import list_suggestions
from ..config import Settings


def _author_line(row: dict) -> str:
    """Собрать строку автора для отчёта."""
    first = (row.get("user_first_name") or "").strip()
    last = (row.get("user_last_name") or "").strip()
    display_name = (f"{first} {last}".strip()) or "пользователь"
    user_id = row.get("user_id") or "?"
    username = row.get("user_username")
    username_part = f" (@{username})" if username else ""
    return f"Автор: {display_name}{username_part} [id:{user_id}]"


def _fmt_row(row: dict) -> str:
    dt = row.get("created_at") or ""
    cat = row.get("category") or "—"
    txt = row.get("text") or ""
    media = row.get("media_type")
    media_tag = " 📎" if media else ""
    dt_s = escape(str(dt))
    cat_s = escape(cat)
    txt_trunc = (txt[:200] + "…") if len(txt) > 200 else txt
    txt_s = escape(txt_trunc) if txt_trunc else "—"
    author = escape(_author_line(row))
    return f"#{row['id']}  ⏱ {dt_s}  |  {cat_s}{media_tag}\n{author}\n{txt_s}"


def _send_report(bot, chat_id: int, title: str, items: list[dict]):
    if not items:
        bot.send_message(chat_id, f"{title}\n\nЗаписей не найдено.", parse_mode="HTML")
        return
    batch = 20
    chunk = []
    for i, it in enumerate(items, 1):
        chunk.append(_fmt_row(it))
        if i % batch == 0:
            bot.send_message(chat_id, f"{title}\n\n" + "\n\n".join(chunk), parse_mode="HTML")
            chunk = []
    if chunk:
        bot.send_message(chat_id, f"{title}\n\n" + "\n\n".join(chunk), parse_mode="HTML")


def _build_and_send(bot, message: types.Message, weekly: bool):
    now = datetime.now()
    if weekly:
        since = now - timedelta(days=7)
        title = "📊 В работе за 7 дней (status = in_process)"
    else:
        since = now - timedelta(days=30)
        title = "📊 В работе за 30 дней (status = in_process)"
    since_str = since.strftime("%Y-%m-%d %H:%M:%S")
    until_str = now.strftime("%Y-%m-%d %H:%M:%S")
    rows = list_suggestions(status="in_process", start=since_str, end=until_str, limit=500)
    _send_report(bot, message.chat.id, title, rows)


def register_handlers(bot):
    @bot.message_handler(commands=["weekly", "monthly"])
    def on_period_report_cmd(message: types.Message):
        managers_chat_id = Settings.managers_chat_id
        if not managers_chat_id or message.chat.id != managers_chat_id:
            bot.send_message(message.chat.id, "⛔ Команда доступна только в менеджерской группе.", parse_mode="HTML")
            return

        try:
            cmd = (message.text or "").split()[0].lower()
            weekly = cmd.startswith("/weekly")
            _build_and_send(bot, message, weekly=weekly)
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Ошибка отчёта: {escape(str(e))}", parse_mode="HTML")
