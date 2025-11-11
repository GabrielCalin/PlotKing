from typing import List, Tuple
import re

def _format_validation_markdown(result: str, details: str, impact_result: str = None, impact_details: str = None, impacted: List[str] = None) -> str:
    """Formatează rezultatul validării într-un format markdown human-readable."""
    
    if result == "ERROR":
        return f"""## ❌ Error

**Validation failed with error:**

```
{details}
```
"""
    
    if result == "UNKNOWN":
        return f"""## ⚠️ Unexpected Format

**Received unexpected validation format:**

```
{details}
```
"""
    
    if result == "NO_CHANGES":
        message = details.split("MESSAGE:", 1)[1].strip() if "MESSAGE:" in details else details
        return f"""## ✅ No Major Changes Detected

{message}
"""
    
    if result == "CHANGES_DETECTED":
        changes_section = ""
        if "CHANGES:" in details:
            changes_text = details.split("CHANGES:", 1)[1].strip()
            changes_lines = [line.strip() for line in changes_text.split("\n") if line.strip() and not line.strip().startswith("RESULT:")]
            if changes_lines:
                changes_section = "### 📝 Changes Detected\n\n"
                for line in changes_lines:
                    if line.startswith("-"):
                        changes_section += f"{line}\n"
                    else:
                        changes_section += f"- {line}\n"
        
        impact_section = ""
        if impact_result == "ERROR":
            impact_section = f"\n\n### ❌ Impact Analysis Error\n\n{impact_details}\n"
        elif impact_result == "UNKNOWN":
            impact_section = f"\n\n### ⚠️ Unexpected Impact Format\n\n{impact_details}\n"
        elif impact_result == "IMPACT_DETECTED":
            impact_section = "\n\n### ⚠️ Impact Analysis\n\n"
            
            if impacted:
                impact_section += f"**Sections that need updates:** {', '.join(f'`{s}`' for s in impacted)}\n\n"
            
            if "IMPACT:" in impact_details:
                impact_text = impact_details.split("IMPACT:", 1)[1].strip()
                impact_items = []
                current_section = None
                current_reason = []
                
                for line in impact_text.split("\n"):
                    line = line.strip()
                    if line.startswith("- Section:"):
                        if current_section:
                            impact_items.append((current_section, "\n".join(current_reason).strip()))
                        current_section = line.replace("- Section:", "").strip()
                        current_reason = []
                    elif line.startswith("Reason:"):
                        reason = line.replace("Reason:", "").strip()
                        if reason:
                            current_reason.append(reason)
                    elif line and current_reason:
                        current_reason.append(line)
                
                if current_section:
                    impact_items.append((current_section, "\n".join(current_reason).strip()))
                
                if impact_items:
                    for section, reason in impact_items:
                        impact_section += f"#### 📌 {section}\n\n{reason}\n\n"
            elif "MESSAGE:" in impact_details:
                message = impact_details.split("MESSAGE:", 1)[1].strip()
                impact_section += f"{message}\n"
        elif impact_result == "NO_IMPACT":
            if "MESSAGE:" in impact_details:
                message = impact_details.split("MESSAGE:", 1)[1].strip()
                impact_section = f"\n\n### ✅ No Impact Detected\n\n{message}\n"
            else:
                impact_section = "\n\n### ✅ No Impact Detected\n\nNo other sections require updates.\n"
        
        return f"""## 📋 Validation Results

{changes_section}{impact_section}
"""
    
    return f"""## ⚠️ Unexpected Result

**Result:** `{result}`

**Details:**
```
{details}
```
"""

def editor_list_sections():
    """Returnează lista secțiunilor existente din checkpoint."""
    from pipeline.state_manager import get_checkpoint
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        return []
    
    sections = []
    
    # Adaugă "Expanded Plot" dacă există
    expanded_plot = checkpoint.get("expanded_plot")
    if expanded_plot and expanded_plot.strip():
        sections.append("Expanded Plot")
    
    # Adaugă "Chapters Overview" dacă există
    chapters_overview = checkpoint.get("chapters_overview")
    if chapters_overview and chapters_overview.strip():
        sections.append("Chapters Overview")
    
    # Adaugă capitolele generate (Chapter 1, Chapter 2, etc.)
    chapters_full = checkpoint.get("chapters_full", [])
    for i in range(len(chapters_full)):
        sections.append(f"Chapter {i + 1}")
    
    return sections

def editor_get_section_content(name):
    """Încarcă textul secțiunii selectate din checkpoint."""
    from pipeline.state_manager import get_checkpoint
    
    if not name:
        return ""
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        return ""
    
    return _section_content_from_checkpoint(checkpoint, name)

def editor_validate(section, draft):
    """Validează modificările comparând versiunea originală cu versiunea editată."""
    from pipeline.state_manager import get_checkpoint
    from pipeline.context import PipelineContext
    from pipeline.steps.version_diff import call_llm_version_diff
    from pipeline.steps.impact_analyzer import call_llm_impact_analysis

    checkpoint = get_checkpoint()
    if not checkpoint:
        return "Error: No checkpoint found.", None

    # Obține versiunea originală din checkpoint (fără să o modificăm)
    original_version = _section_content_from_checkpoint(checkpoint, section) or ""

    # Creează un context temporar din checkpoint pentru a obține genre
    context = PipelineContext.from_checkpoint(checkpoint)

    # Apelează call_llm_version_diff
    result, details = call_llm_version_diff(
        section_type=section,
        original_version=original_version,
        modified_version=draft or "",
        genre=context.genre or "",
    )

    # Formatează rezultatul pentru Validation Output
    if result == "ERROR":
        msg = _format_validation_markdown(result, details)
        plan = None
    elif result == "UNKNOWN":
        msg = _format_validation_markdown(result, details)
        plan = None
    elif result == "NO_CHANGES":
        msg = _format_validation_markdown(result, details)
        plan = None
    elif result == "CHANGES_DETECTED":
        candidates = _build_candidate_sections(section, checkpoint)
        impact_result, impact_details, impacted = call_llm_impact_analysis(
            section_name=section,
            edited_section_content=draft or "",
            diff_summary=details,
            candidate_sections=candidates,
        )
        msg = _format_validation_markdown(result, details, impact_result, impact_details, impacted)
        plan = None
    else:
        msg = _format_validation_markdown(result, details)
        plan = None

    return msg, plan

def editor_apply(section, draft, plan):
    # Aplica modificarea efectivă (în state / fișier) după validare
    saved_text = draft
    preview_text = draft
    
    # Dacă există plan, declanșează pipeline + schimbare tab
    if plan:
        switch_to_create()
        # aici se poate porni pipeline parțial
        switch_to_editor()
    
    return saved_text, preview_text

def force_edit(section, draft):
    """Aplică modificarea direct în checkpoint, fără validare."""
    from pipeline.state_manager import get_checkpoint, save_checkpoint
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        return draft
    
    # Creează o copie a checkpoint-ului pentru a-l actualiza
    updated_checkpoint = checkpoint.copy()
    
    # Actualizează secțiunea corespunzătoare
    if section == "Expanded Plot":
        updated_checkpoint["expanded_plot"] = draft
    elif section == "Chapters Overview":
        updated_checkpoint["chapters_overview"] = draft
    elif section.startswith("Chapter "):
        try:
            chapter_num = int(section.split(" ")[1])
            chapters_full = list(updated_checkpoint.get("chapters_full", []))  # Creează o copie
            # Actualizează doar dacă capitolul există deja
            if 1 <= chapter_num <= len(chapters_full):
                chapters_full[chapter_num - 1] = draft
                updated_checkpoint["chapters_full"] = chapters_full
        except (ValueError, IndexError):
            pass
    
    # Salvează checkpoint-ul actualizat
    save_checkpoint(updated_checkpoint)
    
    return draft

def switch_to_create():
    print(">>> Switching to Create tab... (JS trigger here)")

def switch_to_editor():
    print(">>> Returning to Editor tab... (JS trigger here)")

def _section_content_from_checkpoint(checkpoint, name: str) -> str:
    if not checkpoint or not name:
        return ""

    if name == "Expanded Plot":
        return checkpoint.get("expanded_plot", "") or ""

    if name == "Chapters Overview":
        return checkpoint.get("chapters_overview", "") or ""

    if name.startswith("Chapter "):
        try:
            chapter_num = int(name.split(" ")[1])
            chapters_full = checkpoint.get("chapters_full", [])
            if 1 <= chapter_num <= len(chapters_full):
                return chapters_full[chapter_num - 1] or ""
        except (ValueError, IndexError):
            return ""

    return ""


def _build_candidate_sections(section: str, checkpoint) -> List[Tuple[str, str]]:
    candidates: List[Tuple[str, str]] = []

    if not section:
        return candidates

    def add(name: str):
        if not name or name == section:
            return
        content = _section_content_from_checkpoint(checkpoint, name) or ""
        candidates.append((name, content))

    total_chapters = len(checkpoint.get("chapters_full", []) or [])

    if section in {"Expanded Plot", "Chapters Overview"}:
        add("Expanded Plot")
        add("Chapters Overview")
        for idx in range(1, total_chapters + 1):
            add(f"Chapter {idx}")
    elif section.startswith("Chapter "):
        add("Expanded Plot")
        add("Chapters Overview")
        try:
            chapter_num = int(section.split(" ")[1])
        except (ValueError, IndexError):
            chapter_num = None
        if chapter_num:
            for idx in range(chapter_num + 1, total_chapters + 1):
                add(f"Chapter {idx}")
    else:
        add("Expanded Plot")
        add("Chapters Overview")

    unique: List[Tuple[str, str]] = []
    seen = set()
    for name, content in candidates:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, content))
    return unique
