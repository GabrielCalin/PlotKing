from enum import Enum
from typing import Dict, List, Optional, Any

class DraftType(Enum):
    ORIGINAL = "original"   # Editat de user (Manual/Chat/Rewrite)
    GENERATED = "generated" # Generat de AI (Pipeline)

class DraftsManager:
    """
    Singleton class that manages draft content and metadata for editor sections.
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
        
    def add_original(self, section: str, content: str) -> None:
        """Add a draft marked as ORIGINAL (user edited)."""
        self._drafts[section] = {
            "content": content,
            "type": DraftType.ORIGINAL.value
        }
        
    def add_generated(self, section: str, content: str) -> None:
        """Add a draft marked as GENERATED (AI pipeline)."""
        self._drafts[section] = {
            "content": content,
            "type": DraftType.GENERATED.value
        }
        
    def remove(self, section: str) -> bool:
        """Remove a draft."""
        if section in self._drafts:
            del self._drafts[section]
            return True
        return False
        
    def get_content(self, section: str) -> Optional[str]:
        """Get just the content string."""
        draft = self._drafts.get(section)
        return draft["content"] if draft else None
        
    def get_type(self, section: str) -> Optional[str]:
        """Get the draft type."""
        draft = self._drafts.get(section)
        return draft["type"] if draft else None

    def has(self, section: str) -> bool:
        return section in self._drafts
        
    def get_original_drafts(self) -> List[str]:
        """Get list of section names that are ORIGINAL drafts."""
        return [k for k, v in self._drafts.items() if v["type"] == DraftType.ORIGINAL.value]
        
    def get_generated_drafts(self) -> List[str]:
        """Get list of section names that are GENERATED drafts."""
        return [k for k, v in self._drafts.items() if v["type"] == DraftType.GENERATED.value]

    def get_all_content(self) -> Dict[str, str]:
        """Get all drafts as a simple {section: content} dict."""
        return {k: v["content"] for k, v in self._drafts.items()}

    def update(self, other: 'DraftsManager'):
        """Update from another manager."""
        if isinstance(other, DraftsManager):
            self._drafts.update(other._drafts)
        else:
            raise ValueError("Update expects a DraftsManager instance")
