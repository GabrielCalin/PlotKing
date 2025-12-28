import gradio as gr
import re
import difflib
from typing import List, Dict, Any
from utils.timestamp import ts_prefix
from handlers.editor.rewrite_presets import REWRITE_PRESETS

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

def diff_handler(current_text, initial_text, diff_btn_label, show_label="📝 Show Draft", diff_label="⚖️ Diff"):
    """
    Toggles between Draft view and Diff view.
    Uses paragraph-level diffing with inline word-level diffs for modifications.
    Ignores whitespace-only changes to prevent visual noise.
    """
    if diff_btn_label == diff_label:
        
        # 1. Tokenize by paragraphs (splitting by single newlines), filtering empty strings
        def tokenize_paragraphs(text):
            return [p for p in re.split(r'(\n)', text) if p]

        # 2. Tokenize by words (keeping whitespace)
        def tokenize_words(text):
            return re.split(r'(\s+)', text)

        initial_paras = tokenize_paragraphs(initial_text)
        current_paras = tokenize_paragraphs(current_text)
        
        matcher = difflib.SequenceMatcher(None, initial_paras, current_paras)
        
        html_parts = []
        
        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            if opcode == 'equal':
                # Unchanged paragraphs
                for i in range(a0, a1):
                    html_parts.append(initial_paras[i])
            
            elif opcode == 'delete':
                # Deleted paragraphs
                # Check if it's just whitespace/newlines being deleted
                deleted_text = "".join(initial_paras[a0:a1])
                if not deleted_text.strip():
                    # Ignore whitespace deletion (e.g. extra newlines)
                    continue
                
                for i in range(a0, a1):
                    html_parts.append(f'<div class="diff-del">{initial_paras[i]}</div>')
            
            elif opcode == 'insert':
                # Inserted paragraphs
                # Check if it's just whitespace/newlines being inserted
                inserted_text = "".join(current_paras[b0:b1])
                if not inserted_text.strip():
                    # Append raw whitespace without highlighting
                    html_parts.append(inserted_text)
                    continue

                for i in range(b0, b1):
                    html_parts.append(f'<div class="diff-ins">{current_paras[i]}</div>')
            
            elif opcode == 'replace':
                # Replaced paragraphs
                # If it's a 1-to-1 replacement, try word-level diff
                if (a1 - a0) == 1 and (b1 - b0) == 1:
                    p_old = initial_paras[a0]
                    p_new = current_paras[b0]
                    
                    # If lines are identical ignoring whitespace, just show new one
                    if p_old.strip() == p_new.strip():
                        html_parts.append(p_new)
                        continue

                    w_matcher = difflib.SequenceMatcher(None, tokenize_words(p_old), tokenize_words(p_new))
                    
                    para_html = []
                    for w_opcode, wa0, wa1, wb0, wb1 in w_matcher.get_opcodes():
                        if w_opcode == 'equal':
                            para_html.append("".join(tokenize_words(p_old)[wa0:wa1]))
                        elif w_opcode == 'delete':
                            del_text = "".join(tokenize_words(p_old)[wa0:wa1])
                            if del_text.strip(): # Only highlight if not whitespace
                                para_html.append(f'<span class="diff-del-word">{del_text}</span>')
                        elif w_opcode == 'insert':
                            ins_text = "".join(tokenize_words(p_new)[wb0:wb1])
                            if ins_text.strip(): # Only highlight if not whitespace
                                para_html.append(f'<span class="diff-ins-word">{ins_text}</span>')
                            else:
                                para_html.append(ins_text)
                        elif w_opcode == 'replace':
                            del_text = "".join(tokenize_words(p_old)[wa0:wa1])
                            ins_text = "".join(tokenize_words(p_new)[wb0:wb1])
                            
                            if del_text.strip():
                                para_html.append(f'<span class="diff-del-word">{del_text}</span>')
                            if ins_text.strip():
                                para_html.append(f'<span class="diff-ins-word">{ins_text}</span>')
                            else:
                                para_html.append(ins_text)
                    
                    html_parts.append("".join(para_html))
                else:
                    # Block replacement (too different or multi-paragraph)
                    for i in range(a0, a1):
                        html_parts.append(f'<div class="diff-del">{initial_paras[i]}</div>')
                    for i in range(b0, b1):
                        html_parts.append(f'<div class="diff-ins">{current_paras[i]}</div>')
        
        final_html = "".join(html_parts)
        
        return (
            gr.update(value=final_html), # viewer_md shows diff
            gr.update(value=show_label), # Toggle button label
        )
    else:
        # Revert to Draft view
        return (
            gr.update(value=current_text), # viewer_md shows draft
            gr.update(value=diff_label), # Toggle button label
        )

def format_validation_markdown(
    result: str,
    diff_data: Dict[str, Any],
    impact_result: str = None,
    impact_data: Dict[str, Any] = None,
    impacted: List[str] = None,
) -> str:
    """Formatează rezultatul validării într-un format markdown human-readable."""
    
    if result == "ERROR":
        message = diff_data.get("error", "Unknown error encountered during validation.")
        return f"""## ❌ Error

**Validation failed with error:**

```
{message}
```
"""
    
    if result == "UNKNOWN":
        raw = diff_data.get("raw", "(no details provided)")
        return f"""## ⚠️ Unexpected Format

**Received unexpected validation format:**

```
{raw}
```
"""
    
    if result == "NO_CHANGES":
        message = diff_data.get("message", "No major changes detected.")
        return f"""## ✅ No Major Changes Detected

{message}
"""
    
    if result == "CHANGES_DETECTED":
        changes_section = ""
        changes = diff_data.get("changes", []) or []
        if changes:
            changes_section = "### 📝 Changes Detected\n\n"
            for change in changes:
                if isinstance(change, str):
                    changes_section += f"- {change}\n"
                else:
                    changes_section += f"- {str(change)}\n"
        
        impact_section = ""
        if impact_result == "ERROR":
            message = "Unknown error during impact analysis."
            if impact_data:
                message = impact_data.get("error", message)
            impact_section = f"\n\n### ❌ Impact Analysis Error\n\n{message}\n"
        elif impact_result == "UNKNOWN":
            raw = "(no details provided)"
            if impact_data:
                raw = impact_data.get("raw", raw)
            impact_section = f"\n\n### ⚠️ Unexpected Impact Format\n\n{raw}\n"
        elif impact_result == "IMPACT_DETECTED":
            impact_section = "\n\n### ⚠️ Impact Analysis\n\n"
            
            if impacted:
                impact_section += f"**Sections that need updates:** {', '.join(f'`{s}`' for s in impacted)}\n\n"
            
            items = []
            if impact_data:
                items = impact_data.get("impacted_sections", []) or []

            if items:
                for entry in items:
                    name = entry.get("name") if isinstance(entry, dict) else None
                    reason = entry.get("reason") if isinstance(entry, dict) else None
                    if name:
                        impact_section += f"#### 📌 {name}\n\n{reason or 'Reason not provided.'}\n\n"
            else:
                impact_section += "No impacted sections provided.\n"
        elif impact_result == "NO_IMPACT":
            message = "No other sections require updates."
            if impact_data:
                message = impact_data.get("message", message)
            impact_section = f"\n\n### ✅ No Impact Detected\n\n{message}\n"
        
        return f"""## 📋 Validation Results

{changes_section}{impact_section}
"""
    
    raw_details = diff_data if isinstance(diff_data, str) else str(diff_data)
    return f"""## ⚠️ Unexpected Result

**Result:** `{result}`

**Details:**
```
{raw_details}
```
"""

def keep_draft_handler(section, content, status_log):
    """
    Save the current content as a USER draft and switch to View mode.
    """
    if not section:
        return gr.update(), gr.update(), status_log
        
    from state.drafts_manager import DraftsManager, DraftType
    from handlers.editor.constants import Components, States
    from state.infill_manager import InfillManager
    
    drafts_mgr = DraftsManager()
    im = InfillManager()
    clean_content = remove_highlight(content)
    
    if im.is_fill(section):
        drafts_mgr.add_fill_draft(section, clean_content) # Save as FILL draft if it's a fill section
    else:
        drafts_mgr.add_user_draft(section, clean_content) # Explicitly save as USER draft
        
    drafts_mgr.remove(section, DraftType.CHAT.value) # Remove chat draft if exists, now saved
    
    msg = f"💾 Saved draft for **{section}**."
    new_log, status_update = append_status(status_log, msg)

    # Return updates to switch to View mode and show correct buttons
    draft_display_name = DraftsManager.get_display_name(DraftType.USER.value)
    
    return (
        gr.update(value=clean_content, visible=True), # 1. Viewer MD
        gr.update(value=f"**Viewing:** <span style='color:red;'>{draft_display_name}</span>"), # 2. Status Label
        "Draft", # 3. Current View State
        gr.update(visible=True, interactive=True), # 4. Checkpoint Btn
        gr.update(visible=True, interactive=True), # 5. Draft Btn
        gr.update(visible=True, interactive=True), # 6. Diff Btn
        gr.update(value="View", interactive=True), # 7. Mode Radio
        gr.update(interactive=True), # 8. Section Dropdown
        gr.update(visible=True),     # 9. View Actions Row
        new_log,       # 10. Status Log State (new_log)
        status_update, # 11. Status Strip (text update)
        
        # Hide Manual UI
        gr.update(visible=False), # 12. Start Edit
        gr.update(visible=False), # 13. Confirm
        gr.update(visible=False), # 14. Discard
        gr.update(visible=False), # 15. Force Edit
        gr.update(visible=False), # 16. Keep Draft (Manual)
        
        # Hide Rewrite UI
        gr.update(visible=False), # 17. Rewrite Section
        
        # Hide Chat UI
        gr.update(visible=False), # 18. Chat Section
    )

def sort_drafts(draft_list):
    """
    Sort drafts based on priority:
    1. Expanded Plot
    2. Chapters Overview
    3. Chapter X (Numeric)
    4. Others (Alpha)
    """
    if not draft_list:
        return []
    
    def sort_key(item):
        if item == "Expanded Plot":
            return (0, 0)
        if item == "Chapters Overview":
            return (1, 0)
        
        # Check for Chapter X
        if item.startswith("Chapter "):
            try:
                # Extract number for numeric sort
                parts = item.split(" ")
                if len(parts) > 1 and parts[1].isdigit():
                     return (2, int(parts[1]))
            except:
                pass
        
        return (3, item)

    return sorted(draft_list, key=sort_key)
