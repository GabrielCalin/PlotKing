# -*- coding: utf-8 -*-
# state/transitions_cache.py
"""
Temporary cache for transitions (not persisted in checkpoint).
Used only for UI display purposes.
"""

from threading import Lock
from typing import List, Dict, Any, Optional

_transitions_data: List[Dict[str, Any]] = []
_lock = Lock()


def save_transitions(transitions: List[Dict[str, Any]]) -> None:
    global _transitions_data
    with _lock:
        _transitions_data = list(transitions) if transitions else []


def get_transitions() -> List[Dict[str, Any]]:
    with _lock:
        return list(_transitions_data)


def has_transitions() -> bool:
    with _lock:
        return len(_transitions_data) > 0


def clear_transitions() -> None:
    global _transitions_data
    with _lock:
        _transitions_data = []


def get_transition_for_chapter(chapter_index: int) -> Optional[Dict[str, Any]]:
    with _lock:
        idx = chapter_index - 1
        if 0 <= idx < len(_transitions_data):
            return _transitions_data[idx]
        return None


