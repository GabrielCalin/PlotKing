import gradio as gr
import re
from utils.timestamp import ts_prefix
from ui.rewrite_presets import REWRITE_PRESETS

def append_status(current_log, message):
    """Append message to status log with timestamp."""
    new_line = ts_prefix(message) + "\n"
    updated_log = (current_log or "") + new_line
    return updated_log, gr.update(value=updated_log)

def infer_section_from_counter(counter: str):
    if not counter:
        return None
    if "Expanded Plot" in counter:
        return "Expanded Plot"
    if "Chapters Overview" in counter:
        return "Chapters Overview"
    if "Chapter " in counter:
        # încearcă să extragi numărul
        m = re.search(r"Chapter\s+(\d+)", counter)
        if m:
            return f"Chapter {m.group(1)}"
    return None

def update_instructions_from_preset(preset_name):
    """Update instructions text area based on selected preset."""
    # "None" is now in REWRITE_PRESETS with value "", so we just get it.
    # If preset_name is None (e.g. unselected), we default to empty string or do nothing.
    if preset_name is None:
            return gr.update()
    text = REWRITE_PRESETS.get(preset_name, "")
    return gr.update(value=text)

def format_selected_preview(selected_txt):
    """Format selected text preview - first 25 chars + ... if longer."""
    if not selected_txt:
        return ""
    if len(selected_txt) <= 25:
        return selected_txt
    return selected_txt[:25] + "..."

def replace_text_with_highlight(full_text, start_idx, end_idx, new_text):
    """Replace selected text with new text and wrap new text in red markdown (line by line)."""
    if start_idx is None or end_idx is None:
        return full_text
    
    before = full_text[:start_idx]
    after = full_text[end_idx:]
    
    # Wrap each line individually to ensure highlighting persists across newlines
    lines = new_text.split('\n')
    highlighted_lines = [f'<span style="color: red;">{line}</span>' if line.strip() else line for line in lines]
    highlighted_new = '\n'.join(highlighted_lines)
    
    return before + highlighted_new + after

def remove_highlight(text):
    """Remove red highlighting from text."""
    # Remove span tags but keep content
    return re.sub(r'<span style="color: red;">(.*?)</span>', r'\1', text, flags=re.DOTALL)
