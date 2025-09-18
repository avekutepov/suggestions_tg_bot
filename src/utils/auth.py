from time import time
from typing import Optional, Tuple, Dict
from telebot.apihelper import ApiTelegramException

# Простой TTL-кэш результатов get_chat_member, чтобы не дергать API на каждый месседж
_MEMBER_CACHE: Dict[Tuple[int, int], Tuple[str, float]] = {}  # (chat_id, user_id) -> (status, expires_at)
_TTL_SECONDS = 300  # 5 минут

_ALLOWED_STATUSES = {"member", "administrator", "creator", "restricted"}  # restricted = muted, но все равно «сотрудник»

def _cache_get(chat_id: int, user_id: int) -> Optional[str]:
    key = (chat_id, user_id)
    item = _MEMBER_CACHE.get(key)
    if not item:
        return None
    status, exp = item
    if exp < time():
        _MEMBER_CACHE.pop(key, None)
        return None
    return status

def _cache_put(chat_id: int, user_id: int, status: str):
    _MEMBER_CACHE[(chat_id, user_id)] = (status, time() + _TTL_SECONDS)

def is_user_in_chat(bot, chat_id: Optional[int], user_id: int) -> bool:
    if not chat_id:
        return False
    cached = _cache_get(chat_id, user_id)
    if cached is not None:
        return cached in _ALLOWED_STATUSES
    try:
        m = bot.get_chat_member(chat_id, user_id)
        status = getattr(m, "status", None) or ""
        _cache_put(chat_id, user_id, status)
        return status in _ALLOWED_STATUSES
    except ApiTelegramException:
        # Бот не в чате / нет прав / пользователь не найден
        _cache_put(chat_id, user_id, "unknown")
        return False

def is_allowed_user(bot, user_id: int, *, allowed_chats: Tuple[Optional[int], Optional[int]]):
    """
    Считаем сотрудником, если пользователь состоит хотя бы в одном из чатов:
    - общая группа (public_chat_id)
    - менеджерская группа (managers_chat_id)
    """
    pub, man = allowed_chats
    return is_user_in_chat(bot, pub, user_id) or is_user_in_chat(bot, man, user_id)
