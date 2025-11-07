# ui/__init__.py
from pathlib import Path

_ASSETS_DIR = Path(__file__).parent / "assets"

def load_css(*file_names: str) -> str:
    """
    Load and concatenate one or more CSS files from ui/assets/.
    If no filenames given, defaults to ['style.css'].
    """
    if not file_names:
        file_names = ("style.css",)

    css_parts = []
    for name in file_names:
        path = _ASSETS_DIR / name
        try:
            css_parts.append(path.read_text(encoding="utf-8"))
        except Exception:
            print(f"[WARN] CSS file not found: {path}")
            continue

    return "\n\n".join(css_parts)
