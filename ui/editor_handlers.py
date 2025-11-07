def editor_list_sections():
    # Returnează lista secțiunilor existente
    return ["Expanded Plot", "Chapters Overview", "Chapter 1"]

def editor_get_section_content(name):
    # Încarcă textul secțiunii selectate din proiectul curent
    return f"## {name}\n\nThis is the content of {name}."

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
    # Aplica modificarea efectivă (în state / fișier)
    saved_text = draft
    preview_text = draft
    # Dacă există plan, declanșează pipeline + schimbare tab
    if plan:
        switch_to_create()
        # aici se poate porni pipeline parțial
        switch_to_editor()
    return saved_text, preview_text

def switch_to_create():
    print(">>> Switching to Create tab... (JS trigger here)")

def switch_to_editor():
    print(">>> Returning to Editor tab... (JS trigger here)")
