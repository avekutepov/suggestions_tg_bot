from telebot import types

def kb_moderation(sugg_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"moder:ok:{sugg_id}"),
        types.InlineKeyboardButton("🚫 Отклонить", callback_data=f"moder:rej:{sugg_id}")
    )
    return kb

def kb_moderation_final(text: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text, callback_data="moder:done"))
    return kb

def criteria_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💰 Экономия средств", callback_data="crit_money"))
    kb.add(types.InlineKeyboardButton("⏱ Экономия времени", callback_data="crit_time"))
    kb.add(types.InlineKeyboardButton("⚙ Улучшение процесса", callback_data="crit_process"))
    kb.add(types.InlineKeyboardButton("🛡 Безопасность", callback_data="crit_safety"))
    kb.add(types.InlineKeyboardButton("➕ Другое", callback_data="crit_other"))
    kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="crit_cancel"))
    return kb

def cancel_reply_kb() -> types.ReplyKeyboardMarkup:
    # Без selective и с one_time_keyboard=False, чтобы кнопка точно показалась и не исчезала сама
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.add(types.KeyboardButton("❌ Отмена"))
    return kb

def kb_dm_link(bot_username: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if bot_username:
        kb.add(types.InlineKeyboardButton(
            "✍️ Написать предложение",
            url=f"https://t.me/{bot_username}?start=suggest"
        ))
    return kb
