import os

class Settings:
    bot_token = os.getenv("BOT_TOKEN")
    public_chat_id = int(os.getenv("PUBLIC_CHAT_ID"))
    managers_chat_id = int(os.getenv("MANAGERS_CHAT_ID"))
    allow_media = os.getenv("ALLOW_MEDIA", "true").lower() == "true"