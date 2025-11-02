# ui/ui_state.py
from datetime import datetime

def ts_prefix(message: str) -> str:
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {message}"

def display_selected_chapter(chapter_name, chapters):
    if not chapters or not chapter_name:
        return ""
    try:
        idx = int(chapter_name.split(" ")[1]) - 1
    except Exception:
        return ""
    return chapters[idx] if 0 <= idx < len(chapters) else ""
