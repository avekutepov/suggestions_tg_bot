# ЕДИНОЕ состояние для всего диалога
# _STATE[uid] = {
#   "stage": "await_text" | "await_category_from_text",
#   "category": str | None,
#   "draft_text": str | None,
#   "draft_media": {"type": "...", "file_id": "..."} | None
# }

_STATE: dict[int, dict] = {}


def get(uid: int) -> dict:
    return _STATE.get(uid, {})


def set(uid: int, **kwargs):
    st = _STATE.get(uid, {})
    st.update(kwargs)
    _STATE[uid] = st


def reset(uid: int):
    _STATE.pop(uid, None)


def is_stage(uid: int, stage: str) -> bool:
    return get(uid).get("stage") == stage
