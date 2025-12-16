from state.checkpoint_manager import clear_checkpoint
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

