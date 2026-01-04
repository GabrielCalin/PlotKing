from threading import Lock
from typing import Optional, List
from state.pipeline_context import PipelineContext

_checkpoint_data: Optional[PipelineContext] = None
_lock = Lock()


def save_checkpoint(context: PipelineContext) -> None:
    """Salvează checkpoint-ul complet. Face deep copy pentru liste mutabile."""
    global _checkpoint_data
    with _lock:
        if context is None:
            _checkpoint_data = None
            return
        
        context_copy = PipelineContext(**context.__dict__)
        
        if context_copy.chapters_full:
            context_copy.chapters_full = list(context_copy.chapters_full)
        
        if context_copy.status_log:
            context_copy.status_log = list(context_copy.status_log)
        
        _checkpoint_data = context_copy


def insert_chapter(index: int, content: str) -> bool:
    """
    Inserts a new chapter at the given 1-based index (e.g. 1 inserts at start).
    Shifts existing chapters.
    """
    context = get_checkpoint()
    if not context:
        return False
        
    if not context.chapters_full:
        context.chapters_full = []
        
    # Python insert is 0-indexed.
    # index 1 -> list index 0.
    list_idx = index - 1
    
    # Cap at end
    if list_idx > len(context.chapters_full):
        list_idx = len(context.chapters_full)
    if list_idx < 0:
        list_idx = 0
        
    context.chapters_full.insert(list_idx, content)
    save_checkpoint(context)
    return True


def get_checkpoint() -> Optional[PipelineContext]:
    """Returnează o copie a checkpoint-ului pentru a preveni modificări accidentale."""
    with _lock:
        if _checkpoint_data is None:
            return None
        
        context_copy = PipelineContext(**_checkpoint_data.__dict__)
        
        if context_copy.chapters_full:
            context_copy.chapters_full = list(context_copy.chapters_full)
        
        if context_copy.status_log:
            context_copy.status_log = list(context_copy.status_log)
        
        return context_copy


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
    context = get_checkpoint()
    if not context:
        return False
    
    if section == "Expanded Plot":
        context.expanded_plot = content
    elif section == "Chapters Overview":
        context.chapters_overview = content
    elif section.startswith("Chapter "):
        try:
            chapter_num = int(section.split(" ")[1])
            if not context.chapters_full:
                return False
            if 1 <= chapter_num <= len(context.chapters_full):
                context.chapters_full[chapter_num - 1] = content
            else:
                return False
        except (ValueError, IndexError):
            return False
    else:
        return False
    
    save_checkpoint(context)
    return True


def get_section_content(section: str) -> str:
    """
    Citește conținutul unei secțiuni specifice din checkpoint.
    
    Args:
        section: Numele secțiunii ("Expanded Plot", "Chapters Overview", sau "Chapter N")
    
    Returns:
        Conținutul secțiunii sau string gol dacă nu există
    """
    context = get_checkpoint()
    if not context or not section:
        return ""
    
    if section == "Expanded Plot":
        return context.expanded_plot or ""
    
    if section == "Chapters Overview":
        return context.chapters_overview or ""
    
    if section.startswith("Chapter "):
        try:
            chapter_num = int(section.split(" ")[1])
            if context.chapters_full and 1 <= chapter_num <= len(context.chapters_full):
                return context.chapters_full[chapter_num - 1] or ""
        except (ValueError, IndexError):
            return ""
    
    return ""


def get_sections_list() -> List[str]:
    """
    Returnează lista secțiunilor disponibile în checkpoint.
    
    Returns:
        Lista de nume de secțiuni disponibile
    """
    context = get_checkpoint()
    if not context:
        return []
    
    sections = []
    
    if context.expanded_plot:
        sections.append("Expanded Plot")
    
    if context.chapters_overview:
        sections.append("Chapters Overview")
    
    if context.chapters_full:
        for idx in range(len(context.chapters_full)):
            sections.append(f"Chapter {idx + 1}")
    
    return sections


