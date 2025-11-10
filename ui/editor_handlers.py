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
    
    # Expanded Plot
    if name == "Expanded Plot":
        return checkpoint.get("expanded_plot", "") or ""
    
    # Chapters Overview
    if name == "Chapters Overview":
        return checkpoint.get("chapters_overview", "") or ""
    
    # Chapter N
    if name.startswith("Chapter "):
        try:
            chapter_num = int(name.split(" ")[1])
            chapters_full = checkpoint.get("chapters_full", [])
            if 1 <= chapter_num <= len(chapters_full):
                return chapters_full[chapter_num - 1] or ""
        except (ValueError, IndexError):
            pass
    
    return ""

def editor_validate(section, draft):
    # Exemplu de validare
    if "kill" in draft.lower():
        msg = f"Warning: '{section}' introduces major plot changes."
        plan = {"regen_overview": True, "regen_chapters": [3,4,5]}
    else:
        msg = "OK"
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
    # Aplica modificarea direct, fără validare (Force Edit)
    saved_text = draft
    preview_text = draft
    # Nu declanșează pipeline, aplică direct modificarea
    return saved_text, preview_text

def switch_to_create():
    print(">>> Switching to Create tab... (JS trigger here)")

def switch_to_editor():
    print(">>> Returning to Editor tab... (JS trigger here)")
