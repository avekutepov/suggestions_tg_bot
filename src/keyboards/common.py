from telebot import types

def kb_moderation(sugg_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"moder:approve:{sugg_id}"),
        types.InlineKeyboardButton("🚫 Отклонить", callback_data=f"moder:reject:{sugg_id}"),
    )
    return kb

def criteria_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💰 Экономия средств", callback_data="crit_money"),
        types.InlineKeyboardButton("⏱ Экономия времени",   callback_data="crit_time"),
        types.InlineKeyboardButton("⚙ Улучшение процесса", callback_data="crit_process"),
        types.InlineKeyboardButton("🛡 Безопасность",       callback_data="crit_safety"),
        types.InlineKeyboardButton("➕ Другое",             callback_data="crit_other"),
    )
    kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="crit_cancel"))
    return kb

def cancel_reply_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, selective=True)
    kb.add(types.KeyboardButton("❌ Отмена"))
    return kb


def kb_dm_link(bot_username: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if bot_username:
        kb.add(types.InlineKeyboardButton(
            "✍️ Написать пожелание",
            url=f"https://t.me/{bot_username}?start=suggest"
        ))
    return kb