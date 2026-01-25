# -*- coding: utf-8 -*-
# handlers/create/utils.py

from typing import Dict, Any, List, Optional


def display_selected_chapter(chapter_name, chapters):
    if not chapters or not chapter_name:
        return ""
    try:
        idx = int(chapter_name.split(" ")[1]) - 1
    except Exception:
        return ""
    return chapters[idx] if 0 <= idx < len(chapters) else ""


