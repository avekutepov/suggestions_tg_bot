import re
from datetime import datetime, timedelta, timezone

def sanitize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def human_now() -> str:
    tz = timezone(timedelta(hours=5))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M")