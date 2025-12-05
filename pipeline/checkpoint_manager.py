from threading import Lock
from typing import Optional, Dict, List, Any

_checkpoint_data: Optional[Dict[str, Any]] = None
_lock = Lock()


def save_checkpoint(data: Dict[str, Any]) -> None:
    """Salvează checkpoint-ul complet. Face deep copy pentru liste mutabile."""
    global _checkpoint_data
    with _lock:
        if data is None:
            _checkpoint_data = None
            return
        
        checkpoint_copy = data.copy()
        
        if "chapters_full" in checkpoint_copy and isinstance(checkpoint_copy["chapters_full"], list):
            checkpoint_copy["chapters_full"] = list(checkpoint_copy["chapters_full"])
        
        if "status_log" in checkpoint_copy and isinstance(checkpoint_copy["status_log"], list):
            checkpoint_copy["status_log"] = list(checkpoint_copy["status_log"])
        
        _checkpoint_data = checkpoint_copy


def get_checkpoint() -> Optional[Dict[str, Any]]:
    """Returnează o copie a checkpoint-ului pentru a preveni modificări accidentale."""
    with _lock:
        if _checkpoint_data is None:
            return None
        
        checkpoint_copy = _checkpoint_data.copy()
        
        if "chapters_full" in checkpoint_copy and isinstance(checkpoint_copy["chapters_full"], list):
            checkpoint_copy["chapters_full"] = list(checkpoint_copy["chapters_full"])
        
        if "status_log" in checkpoint_copy and isinstance(checkpoint_copy["status_log"], list):
            checkpoint_copy["status_log"] = list(checkpoint_copy["status_log"])
        
        return checkpoint_copy


def clear_checkpoint() -> None:
    """Șterge checkpoint-ul."""
    global _checkpoint_data
    with _lock:
        _checkpoint_data = None


def has_checkpoint() -> bool:
    """Verifică dacă există un checkpoint."""
    with _lock:
        return _checkpoint_data is not None


def save_section(section: str, content: str) -> bool:
    """
    Salvează conținutul unei secțiuni specifice în checkpoint.
    
    Args:
        section: Numele secțiunii ("Expanded Plot", "Chapters Overview", sau "Chapter N")
        content: Conținutul secțiunii de salvat
    
    Returns:
        True dacă salvarea a reușit, False altfel
    """
    checkpoint = get_checkpoint()
    if not checkpoint:
        return False
    
    updated_checkpoint = checkpoint.copy()
    
    if section == "Expanded Plot":
        updated_checkpoint["expanded_plot"] = content
    elif section == "Chapters Overview":
        updated_checkpoint["chapters_overview"] = content
    elif section.startswith("Chapter "):
        try:
            chapter_num = int(section.split(" ")[1])
            chapters_full = list(updated_checkpoint.get("chapters_full", []))
            if 1 <= chapter_num <= len(chapters_full):
                chapters_full[chapter_num - 1] = content
                updated_checkpoint["chapters_full"] = chapters_full
            else:
                return False
        except (ValueError, IndexError):
            return False
    else:
        return False
    
    save_checkpoint(updated_checkpoint)
    return True


def get_section_content(section: str) -> str:
    """
    Citește conținutul unei secțiuni specifice din checkpoint.
    
    Args:
        section: Numele secțiunii ("Expanded Plot", "Chapters Overview", sau "Chapter N")
    
    Returns:
        Conținutul secțiunii sau string gol dacă nu există
    """
    checkpoint = get_checkpoint()
    if not checkpoint or not section:
        return ""
    
    if section == "Expanded Plot":
        return checkpoint.get("expanded_plot", "") or ""
    
    if section == "Chapters Overview":
        return checkpoint.get("chapters_overview", "") or ""
    
    if section.startswith("Chapter "):
        try:
            chapter_num = int(section.split(" ")[1])
            chapters_full = checkpoint.get("chapters_full", [])
            if 1 <= chapter_num <= len(chapters_full):
                return chapters_full[chapter_num - 1] or ""
        except (ValueError, IndexError):
            return ""
    
    return ""


def get_sections_list() -> List[str]:
    """
    Returnează lista secțiunilor disponibile în checkpoint.
    
    Returns:
        Lista de nume de secțiuni disponibile
    """
    checkpoint = get_checkpoint()
    if not checkpoint:
        return []
    
    sections = []
    
    if checkpoint.get("expanded_plot"):
        sections.append("Expanded Plot")
    
    if checkpoint.get("chapters_overview"):
        sections.append("Chapters Overview")
    
    chapters_full = checkpoint.get("chapters_full", [])
    for idx in range(len(chapters_full)):
        sections.append(f"Chapter {idx + 1}")
    
    return sections


