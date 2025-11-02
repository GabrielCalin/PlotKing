# ui/__init__.py
from pathlib import Path

_ASSETS_DIR = Path(__file__).parent / "assets"

def load_css(file_name: str = "style.css") -> str:
    path = _ASSETS_DIR / file_name
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""
