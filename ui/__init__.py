import os

def load_css(file_name="style.css"):
    path = os.path.join(os.path.dirname(__file__), file_name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
