from typing import Optional, Dict, Any

def send_media_with_caption(
    bot,
    chat_id: int,
    draft_media: Optional[Dict[str, Any]],
    caption: str,
    reply_markup=None,
    parse_mode: str = "HTML",
):
    if not draft_media:
        bot.send_message(chat_id, caption, parse_mode=parse_mode, reply_markup=reply_markup)
        return

    t = (draft_media.get("type") or "").lower()
    fid = draft_media.get("file_id")

    if t == "photo":
        bot.send_photo(chat_id, fid, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
    elif t == "video":
        bot.send_video(chat_id, fid, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
    elif t == "document":
        bot.send_document(chat_id, fid, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
    elif t == "voice":
        bot.send_voice(chat_id, fid, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
    elif t == "audio":
        bot.send_audio(chat_id, fid, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
    elif t == "animation":
        bot.send_animation(chat_id, fid, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
    else:
        bot.send_message(chat_id, caption, parse_mode=parse_mode, reply_markup=reply_markup)
