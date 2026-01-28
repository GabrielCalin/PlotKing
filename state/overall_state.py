from state.checkpoint_manager import clear_checkpoint, get_section_content, get_sections_list as get_checkpoint_sections, get_checkpoint
from state.drafts_manager import DraftsManager
from state.pipeline_state import clear_stop, clear_paused
from state.transitions_manager import clear_transitions
from handlers.create.project_manager import set_current_project
from typing import List

def reset_all_states():
    """
    Resetează toate stările aplicației la refresh.
    """
    set_current_project(None)
    clear_checkpoint()
    DraftsManager().clear()
    clear_stop()
    clear_paused()
    clear_transitions()

def get_current_section_content(section: str) -> str:
    """Get current content for section: draft if exists, else checkpoint.
    Uses priority: GENERATED > CHAT > USER > ORIGINAL (via drafts_manager.get_content).
    Falls back to checkpoint if no draft exists.
    """
    drafts_mgr = DraftsManager()
    if drafts_mgr.has(section):
        return drafts_mgr.get_content(section) or ""
    return get_section_content(section) or ""

def get_sections_list() -> List[str]:
    """
    Unified sections list: Checkpoint sections + Interleaved Fill drafts.
    """
    # 1. Get Base Sections
    base_sections = get_checkpoint_sections()
    
    # 2. Get Fills
    dm = DraftsManager()
    fill_keys = dm.get_fill_drafts()
    
    if not fill_keys:
        return base_sections

    # 3. Sort Fills
    def parse_fill_sort_key(name):
        try:
            parts = name.split(" ")
            x = int(parts[1])
            y = int(parts[2].strip("(#)"))
            return (x, y)
        except:
            return (9999, 9999)

    fill_keys.sort(key=parse_fill_sort_key)
    
    # 4. Interleave
    final_items = []
    
    # Indices for base sections
    for s in base_sections:
        if s == "Expanded Plot":
            final_items.append((-2000, s))
        elif s == "Chapters Overview":
            final_items.append((-1000, s))
        elif s.startswith("Chapter "):
            try:
                idx = int(s.split(" ")[1])
                final_items.append((idx * 1000, s))
            except:
                pass
                
    # Indices for fills (Before Chapter X -> X*1000 - 500 + Y)
    for f in fill_keys:
        x, y = parse_fill_sort_key(f)
        sort_score = (x * 1000) - 500 + y
        final_items.append((sort_score, f))
        
    final_items.sort(key=lambda item: item[0])
    
    return [item[1] for item in final_items]


