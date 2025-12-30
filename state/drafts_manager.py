from enum import Enum
from typing import Dict, List, Optional, Any

class DraftType(Enum):
    ORIGINAL = "original"   # Snapshot for validation (checkpoint content at start of flow)
    GENERATED = "generated" # Generat de AI (Pipeline)
    CHAT = "chat"           # Draft din conversatie chat
    USER = "user"           # Draft explicit salvat de user (Keep Draft)
    FILL = "fill"           # New Empty Chapter Fill

class DraftsManager:
    """
    Singleton class that manages draft content and metadata for editor sections.
    Structure: _drafts[section] = { "user": "content...", "generated": "content...", "original": "content..." }
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DraftsManager, cls).__new__(cls)
            cls._instance._drafts = {}
        return cls._instance
    
    def __init__(self):
        # Init called every time class is instantiated, but we only want to init _drafts once in __new__
        pass
        
    def clear(self) -> None:
        """Clear all drafts (e.g. on new project)."""
        self._drafts.clear()

    def get_all_draft_keys(self) -> List[str]:
        """Return list of all sections currently having any draft."""
        return list(self._drafts.keys())
    
    def get_draft_keys_by_type(self, draft_type: str) -> List[str]:
        """Get list of section names that have a draft of the specified type."""
        return [s for s, d in self._drafts.items() if draft_type in d]

    def keep_only_draft_types(self, sections: List[str], draft_types_to_keep: List[str]) -> None:
        """
        Clear drafts for the specified sections, keeping only the specified draft types.
        Preserves only the draft types in draft_types_to_keep and does not touch sections not in the list.
        
        Args:
            sections: List of section names to process
            draft_types_to_keep: List of draft type values to preserve (e.g., [DraftType.USER.value, DraftType.FILL.value])
        """
        for section in sections:
            if section in self._drafts:
                # Remove all types except those in draft_types_to_keep
                for dtype in list(self._drafts[section].keys()):
                    if dtype not in draft_types_to_keep:
                        del self._drafts[section][dtype]
                
                # If section empty now, remove it
                if not self._drafts[section]:
                    del self._drafts[section]
        
    def add_original(self, section: str, content: str) -> None:
        """Add a draft marked as ORIGINAL (snapshot for validation)."""
        if section not in self._drafts:
            self._drafts[section] = {}
        self._drafts[section][DraftType.ORIGINAL.value] = content

    def add_user_draft(self, section: str, content: str) -> None:
        """Add a draft marked as USER (explicit keep draft)."""
        if section not in self._drafts:
            self._drafts[section] = {}
        
        # History tracking
        from state.undo_manager import UndoManager
        if DraftType.USER.value in self._drafts[section]:
            old_content = self._drafts[section][DraftType.USER.value]
            UndoManager().register_change(section, DraftType.USER.value, old_content)
            
        self._drafts[section][DraftType.USER.value] = content

    def add_fill_draft(self, section: str, content: str = "") -> None:
        """Add a FILL draft."""
        if section not in self._drafts:
            self._drafts[section] = {}
            
        from state.undo_manager import UndoManager
        if DraftType.FILL.value in self._drafts[section]:
            old_content = self._drafts[section][DraftType.FILL.value]
            UndoManager().register_change(section, DraftType.FILL.value, old_content)
            
        self._drafts[section][DraftType.FILL.value] = content
        
    def add_generated(self, section: str, content: str) -> None:
        """Add a draft marked as GENERATED (AI pipeline)."""
        if section not in self._drafts:
            self._drafts[section] = {}
            
        # History tracking
        from state.undo_manager import UndoManager
        if DraftType.GENERATED.value in self._drafts[section]:
            old_content = self._drafts[section][DraftType.GENERATED.value]
            UndoManager().register_change(section, DraftType.GENERATED.value, old_content)
            
        self._drafts[section][DraftType.GENERATED.value] = content

    def add_chat(self, section: str, content: str) -> None:
        """Add a draft marked as CHAT (Chat session)."""
        if section not in self._drafts:
            self._drafts[section] = {}
            
        # History tracking
        from state.undo_manager import UndoManager
        if DraftType.CHAT.value in self._drafts[section]:
            old_content = self._drafts[section][DraftType.CHAT.value]
            UndoManager().register_change(section, DraftType.CHAT.value, old_content)

        self._drafts[section][DraftType.CHAT.value] = content
        
    def remove(self, section: str, draft_type: str = None) -> bool:
        """
        Remove drafts.
        If draft_type is provided, remove only that specific draft type.
        If draft_type is None, remove ALL drafts for the section.
        """
        from state.undo_manager import UndoManager

        if section not in self._drafts:
            return False
            
        if draft_type:
            if draft_type in self._drafts[section]:
                del self._drafts[section][draft_type]
                
                # Clear history for this type
                UndoManager().clear_history(section, draft_type)
                
                # If section dict empty, remove section key
                if not self._drafts[section]:
                    del self._drafts[section]
                return True
            return False
        else:
            # Clear ALL history for this section before removing it
            UndoManager().clear_history(section)
            
            # Remove entire section entry
            del self._drafts[section]
            return True

    def set_content_no_history(self, section: str, draft_type: str, content: str) -> None:
        """
        Set draft content WITHOUT triggering UndoManager history push.
        Used by UndoManager to restore previous versions.
        """
        if section not in self._drafts:
            self._drafts[section] = {}
        self._drafts[section][draft_type] = content
        
    def get_content(self, section: str, draft_type: str = None) -> Optional[str]:
        """
        Get draft content.
        If draft_type is specified, return that content.
        If NOT specified, return based on Priority: GENERATED > USER > ORIGINAL.
        """
        if section not in self._drafts:
            return None
            
        drafts = self._drafts[section]
        
        if draft_type:
            return drafts.get(draft_type)
            
        # Priority Fallback
        if DraftType.GENERATED.value in drafts:
            # AI Proposal takes precedence in UI by default
            return drafts[DraftType.GENERATED.value]
        if DraftType.CHAT.value in drafts:
            # Chat session changes
            return drafts[DraftType.CHAT.value]
        if DraftType.USER.value in drafts:
            # User manual edit
            return drafts[DraftType.USER.value]
        if DraftType.FILL.value in drafts:
            # Specific Fill content
            return drafts[DraftType.FILL.value]
        if DraftType.ORIGINAL.value in drafts:
            # Snapshot
            return drafts[DraftType.ORIGINAL.value]
            
        return None
        
    def has_type(self, section: str, draft_type: str) -> bool:
        """Check if a specific draft type exists for the section."""
        if section not in self._drafts:
            return False
        return draft_type in self._drafts[section]

    def get_type(self, section: str) -> Optional[str]:
        """
        Get the 'primary' draft type present, following priority:
        GENERATED > USER > ORIGINAL.
        Used for determining UI state (View Actions compatibility).
        """
        if section not in self._drafts:
            return None
        drafts = self._drafts[section]
        
        if DraftType.GENERATED.value in drafts:
            return DraftType.GENERATED.value
        if DraftType.CHAT.value in drafts:
            return DraftType.CHAT.value
        if DraftType.USER.value in drafts:
            return DraftType.USER.value
        if DraftType.FILL.value in drafts:
            return DraftType.FILL.value
        if DraftType.ORIGINAL.value in drafts:
            return DraftType.ORIGINAL.value
        return None

    @staticmethod
    def get_display_name(draft_type: Optional[str]) -> str:
        """Get display name for draft type: capitalize first letter + ' Draft'."""
        if not draft_type:
            return "Draft"
        return draft_type.capitalize() + " Draft"

    def has(self, section: str) -> bool:
        """Check if ANY draft exists for section."""
        return section in self._drafts and bool(self._drafts[section])
    
    def move_all_drafts(self, old_section: str, new_section: str) -> bool:
        """
        Move all drafts from old_section to new_section.
        Returns True if move was successful, False if old_section had no drafts.
        """
        if old_section not in self._drafts or not self._drafts[old_section]:
            return False
        
        old_drafts = self._drafts[old_section].copy()
        
        for draft_type, content in old_drafts.items():
            if draft_type == DraftType.FILL.value:
                self.add_fill_draft(new_section, content)
            elif draft_type == DraftType.USER.value:
                self.add_user_draft(new_section, content)
            elif draft_type == DraftType.GENERATED.value:
                self.add_generated(new_section, content)
            elif draft_type == DraftType.CHAT.value:
                self.add_chat(new_section, content)
            elif draft_type == DraftType.ORIGINAL.value:
                self.add_original(new_section, content)
        
        self.remove(old_section)
        return True
    
    def shift_chapters_after_insert(self, inserted_chapter_index: int) -> None:
        """
        When a chapter is inserted at index, shift all existing chapters with index >= inserted_chapter_index.
        Chapter X -> Chapter X+1, preserving all draft types and content.
        """
        all_sections = list(self._drafts.keys())
        chapter_sections = [s for s in all_sections if s.startswith("Chapter ")]
        
        def get_chapter_index(section_name: str) -> Optional[int]:
            try:
                parts = section_name.split(" ")
                if len(parts) == 2 and parts[0] == "Chapter":
                    return int(parts[1])
            except (ValueError, IndexError):
                pass
            return None
        
        chapter_sections_with_index = [(s, get_chapter_index(s)) for s in chapter_sections]
        chapter_sections_with_index = [(s, idx) for s, idx in chapter_sections_with_index if idx is not None]
        chapter_sections_with_index.sort(key=lambda x: x[1], reverse=True)
        
        for old_section, chapter_idx in chapter_sections_with_index:
            if chapter_idx >= inserted_chapter_index:
                new_section = f"Chapter {chapter_idx + 1}"
                self.move_all_drafts(old_section, new_section)
        
    def get_original_drafts(self) -> List[str]:
        """Get list of section names that have an ORIGINAL draft."""
        return [s for s, d in self._drafts.items() if DraftType.ORIGINAL.value in d]
        
    def get_generated_drafts(self) -> List[str]:
        """Get list of section names that have a GENERATED draft."""
        return self.get_draft_keys_by_type(DraftType.GENERATED.value)

    def get_user_drafts(self) -> List[str]:
        """Get list of section names that have a USER draft."""
        return self.get_draft_keys_by_type(DraftType.USER.value)

    def get_chat_drafts(self) -> List[str]:
        """Get list of section names that have a CHAT draft."""
        return self.get_draft_keys_by_type(DraftType.CHAT.value)
        
    def get_fill_drafts(self) -> List[str]:
        """Get list of section names that have a FILL draft."""
        return self.get_draft_keys_by_type(DraftType.FILL.value)

    def get_all_content(self) -> Dict[str, str]:
        """
        Get simplified {section: content} dict for 'Accept All'.
        Uses priority: GENERATED > USER > ORIGINAL.
        """
        result = {}
        for section in self._drafts:
            content = self.get_content(section)
            if content is not None:
                result[section] = content
        return result

    def update(self, other: 'DraftsManager'):
        """Update from another manager or dict."""
        if isinstance(other, DraftsManager):
            # Deep merge: don't wipe existing types if other has different ones
            for section, drafts_dict in other._drafts.items():
                if section not in self._drafts:
                    self._drafts[section] = {}
                self._drafts[section].update(drafts_dict)
        else:
            # Handle dictionary update (from pipeline results -> GENERATED drafts)
            if isinstance(other, dict):
                for k, v in other.items():
                    self.add_generated(k, v)
            else:
                 raise ValueError("Update expects a DraftsManager instance or dict")
