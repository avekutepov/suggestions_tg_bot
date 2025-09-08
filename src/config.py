import os

def _to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")

class Settings:
    bot_token = os.getenv("BOT_TOKEN", "")

    public_chat_id   = _to_int(os.getenv("PUBLIC_CHAT_ID"),   default=None)
    managers_chat_id = _to_int(os.getenv("MANAGERS_CHAT_ID"), default=None)

    allow_media = _to_bool(os.getenv("ALLOW_MEDIA"), default=True)

    public_chat_username = os.getenv("PUBLIC_CHAT_USERNAME", None)