from telebot import types

def kb_moderation() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Одобрить", callback_data="approve"),
        types.InlineKeyboardButton("🚫 Отклонить", callback_data="reject"),
    )
    return kb

def kb_dm_link(bot_username: str, payload: str = "from_group") -> types.InlineKeyboardMarkup:
    """
    Кнопка «✍️ Написать пожелание» — ведёт в ЛС к боту (deep link).
    Если username пустой — вернётся пустая клавиатура.
    """
    kb = types.InlineKeyboardMarkup()
    if bot_username:
        deep_link = f"https://t.me/{bot_username}?start={payload}"
        kb.add(types.InlineKeyboardButton("✍️ Написать пожелание", url=deep_link))
    return kb