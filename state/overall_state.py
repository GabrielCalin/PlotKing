from state.checkpoint_manager import clear_checkpoint, get_section_content
from state.drafts_manager import DraftsManager
from state.pipeline_state import clear_stop, clear_paused
from handlers.create.project_manager import set_current_project

def reset_all_states():
    """
    Resetează toate stările aplicației la refresh.
    """
    set_current_project(None)
    clear_checkpoint()
    DraftsManager().clear()
    clear_stop()
    clear_paused()

def get_current_section_content(section: str) -> str:
    """Get current content for section: draft if exists, else checkpoint.
    Uses priority: GENERATED > CHAT > USER > ORIGINAL (via drafts_manager.get_content).
    Falls back to checkpoint if no draft exists.
    """
    drafts_mgr = DraftsManager()
    if drafts_mgr.has(section):
        return drafts_mgr.get_content(section) or ""
    return get_section_content(section) or ""

