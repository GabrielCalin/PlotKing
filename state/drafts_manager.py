from enum import Enum
from typing import Dict, List, Optional, Any

class DraftType(Enum):
    ORIGINAL = "original"   # Snapshot for validation (checkpoint content at start of flow)
    GENERATED = "generated" # Generat de AI (Pipeline)
    CHAT = "chat"           # Draft din conversatie chat
    USER = "user"           # Draft explicit salvat de user (Keep Draft)

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

    def keep_only_user_drafts(self, sections: List[str]) -> None:
        """
        Clear only GENERATED, CHAT, and ORIGINAL drafts for the specified sections.
        Preserves USER drafts and does not touch sections not in the list.
        """
        for section in sections:
            if section in self._drafts:
                # Remove all types except USER
                for dtype in list(self._drafts[section].keys()):
                    if dtype != DraftType.USER.value:
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
        self._drafts[section][DraftType.USER.value] = content
        
    def add_generated(self, section: str, content: str) -> None:
        """Add a draft marked as GENERATED (AI pipeline)."""
        if section not in self._drafts:
            self._drafts[section] = {}
        self._drafts[section][DraftType.GENERATED.value] = content

    def add_chat(self, section: str, content: str) -> None:
        """Add a draft marked as CHAT (Chat session)."""
        if section not in self._drafts:
            self._drafts[section] = {}
        self._drafts[section][DraftType.CHAT.value] = content
        
    def remove(self, section: str, draft_type: str = None) -> bool:
        """
        Remove drafts.
        If draft_type is provided, remove only that specific draft type.
        If draft_type is None, remove ALL drafts for the section.
        """
        if section not in self._drafts:
            return False
            
        if draft_type:
            if draft_type in self._drafts[section]:
                del self._drafts[section][draft_type]
                # If section dict empty, remove section key
                if not self._drafts[section]:
                    del self._drafts[section]
                return True
            return False
        else:
            # Remove entire section entry
            del self._drafts[section]
            return True
        
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
        if DraftType.ORIGINAL.value in drafts:
            return DraftType.ORIGINAL.value
        return None

    def has(self, section: str) -> bool:
        """Check if ANY draft exists for section."""
        return section in self._drafts and bool(self._drafts[section])
        
    def get_original_drafts(self) -> List[str]:
        """Get list of section names that have an ORIGINAL draft."""
        return [s for s, d in self._drafts.items() if DraftType.ORIGINAL.value in d]
        
    def get_generated_drafts(self) -> List[str]:
        """Get list of section names that have a GENERATED draft."""
        return [s for s, d in self._drafts.items() if DraftType.GENERATED.value in d]

    def get_user_drafts(self) -> List[str]:
        """Get list of section names that have a USER draft."""
        return [s for s, d in self._drafts.items() if DraftType.USER.value in d]

    def get_chat_drafts(self) -> List[str]:
        """Get list of section names that have a CHAT draft."""
        return [s for s, d in self._drafts.items() if DraftType.CHAT.value in d]

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
