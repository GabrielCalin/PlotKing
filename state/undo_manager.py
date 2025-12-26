from typing import Dict, List, Optional, Tuple, Any

class UndoManager:
    """
    Singleton class that manages undo/redo stacks for editor drafts.
    Structure: _stacks[section][draft_type] = { "undo": [content1, ...], "redo": [content_n, ...] }
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UndoManager, cls).__new__(cls)
            cls._instance._stacks = {}
        return cls._instance

    def register_change(self, section: str, draft_type: str, old_content: str) -> None:
        """
        Register a change: push old content to UNDO stack, clear REDO stack.
        """
        if not section or not draft_type:
            return

        if section not in self._stacks:
            self._stacks[section] = {}
            
        if draft_type not in self._stacks[section]:
            self._stacks[section][draft_type] = {"undo": [], "redo": []}
            
        # Push old content to undo
        self._stacks[section][draft_type]["undo"].append(old_content)
        # Clear redo stack (standard editor behavior)
        self._stacks[section][draft_type]["redo"] = []

    def undo(self, section: str, draft_type: str) -> None:
        """
        Perform Undo:
        1. Get current content from DraftsManager (push to REDO).
        2. Pop from UNDO stack.
        3. Set popped content in DraftsManager (using set_content_no_history).
        """
        if not self.has_undo(section, draft_type):
            return

        from state.drafts_manager import DraftsManager
        dm = DraftsManager()
        
        # 1. Get current content
        current_content = dm.get_content(section, draft_type)
        if current_content is None:
            return # Should not happen if history exists
            
        # 2. Pop from UNDO
        prev_content = self._stacks[section][draft_type]["undo"].pop()
        
        # Push current to REDO
        self._stacks[section][draft_type]["redo"].append(current_content)
        
        # 3. Update DM
        dm.set_content_no_history(section, draft_type, prev_content)

    def redo(self, section: str, draft_type: str) -> None:
        """
        Perform Redo:
        1. Get current content from DraftsManager (push to UNDO).
        2. Pop from REDO stack.
        3. Set popped content in DraftsManager (using set_content_no_history).
        """
        if not self.has_redo(section, draft_type):
            return

        from state.drafts_manager import DraftsManager
        dm = DraftsManager()
        
        # 1. Get current content
        current_content = dm.get_content(section, draft_type)
        
        # 2. Pop from REDO
        next_content = self._stacks[section][draft_type]["redo"].pop()
        
        # Push current to UNDO
        self._stacks[section][draft_type]["undo"].append(current_content)
        
        # 3. Update DM
        dm.set_content_no_history(section, draft_type, next_content)

    def clear_history(self, section: str, draft_type: str = None) -> None:
        """Clear history for a section (specific type or all)."""
        if section not in self._stacks:
            return
            
        if draft_type:
            if draft_type in self._stacks[section]:
                del self._stacks[section][draft_type]
            if not self._stacks[section]:
                del self._stacks[section]
        else:
            del self._stacks[section]

    def has_undo(self, section: str, draft_type: str) -> bool:
        """Check if undo is possible."""
        if section not in self._stacks or draft_type not in self._stacks[section]:
            return False
        return len(self._stacks[section][draft_type]["undo"]) > 0

    def has_redo(self, section: str, draft_type: str) -> bool:
        """Check if redo is possible."""
        if section not in self._stacks or draft_type not in self._stacks[section]:
            return False
        return len(self._stacks[section][draft_type]["redo"]) > 0

    def get_counts(self, section: str, draft_type: str) -> Tuple[int, int]:
        """
        Get (current_index, total_count) for display (e.g., 'Draft 3/5').
        1-based indexing.
        Current index = len(undo) + 1
        Total = len(undo) + 1 (current) + len(redo)
        """
        if section not in self._stacks or draft_type not in self._stacks[section]:
            return 1, 1
            
        undo_count = len(self._stacks[section][draft_type]["undo"])
        redo_count = len(self._stacks[section][draft_type]["redo"])
        
        current_index = undo_count + 1
        total_count = undo_count + 1 + redo_count
        
        return current_index, total_count
