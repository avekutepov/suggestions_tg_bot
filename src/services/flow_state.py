# Один источник правды для состояния диалога

from typing import Optional, Dict, Any

# _STATE[user_id] = {
#   "stage": "await_text" | "await_category_from_text",
#   "category": Optional[str],
#   "draft_text": Optional[str],
#   "draft_media": Optional[Dict[str, str]],  # {"type": "...", "file_id": "..."}
# }
_STATE: Dict[int, Dict[str, Any]] = {}


def reset(user_id: int) -> None:
    _STATE.pop(user_id, None)


def set_await_text(user_id: int, category: str) -> None:
    _STATE[user_id] = {"stage": "await_text", "category": category}


def set_await_category_from_text(user_id: int,
                                 draft_text: str,
                                 draft_media: Optional[Dict[str, str]]) -> None:
    _STATE[user_id] = {
        "stage": "await_category_from_text",
        "category": None,
        "draft_text": draft_text,
        "draft_media": draft_media,
    }


def stage(user_id: int) -> Optional[str]:
    return (_STATE.get(user_id) or {}).get("stage")


def pop_category(user_id: int) -> Optional[str]:
    data = _STATE.get(user_id) or {}
    cat = data.get("category")
    reset(user_id)
    return cat


def get_draft(user_id: int) -> Dict[str, Any]:
    return _STATE.get(user_id, {})


def pop_draft(user_id: int) -> Dict[str, Any]:
    data = _STATE.pop(user_id, {})
    return {
        "draft_text": data.get("draft_text") or "",
        "draft_media": data.get("draft_media"),
    }
