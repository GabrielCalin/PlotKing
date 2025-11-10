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
    """Validează modificările comparând versiunea originală cu versiunea editată."""
    from pipeline.state_manager import get_checkpoint
    from pipeline.context import PipelineContext
    from pipeline.steps.version_diff import call_llm_version_diff
    
    checkpoint = get_checkpoint()
    if not checkpoint:
        return "Error: No checkpoint found.", None
    
    # Obține versiunea originală din checkpoint (fără să o modificăm)
    original_version = editor_get_section_content(section) or ""
    
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
        msg = f"❌ Error during validation: {details}"
        plan = None
    elif result == "UNKNOWN":
        msg = f"⚠️ Unexpected validation format:\n\n{details}"
        plan = None
    elif result == "NO_CHANGES":
        msg = f"✅ {details}"
        plan = None
    elif result == "CHANGES_DETECTED":
        msg = details
        plan = None  # Plan-ul va fi determinat de alt AI ulterior
    else:
        msg = f"⚠️ Unexpected result: {result}\n\n{details}"
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
