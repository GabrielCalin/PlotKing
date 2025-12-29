from threading import Lock
from typing import Optional, List
from state.drafts_manager import DraftsManager, DraftType

class InfillManager:
    """
    Singleton for managing 'Fill' drafts (new chapters inserted between sections).
    Structure of a Fill Name: "Fill X (#Y)"
    - X: The chapter index it will become (or 1 if before Chapter 1).
    - Y: The fill index for that position (allows multiple fills in sequence before commit).
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(InfillManager, cls).__new__(cls)
        return cls._instance

    def create_fill(self, current_section: Optional[str]) -> str:
        """
        Create a new FILL draft based on the currently selected section.
        Returns the name of the new fill section.
        """
        target_chapter_index = 1 # Default if unknown or Chapters Overview
        fill_number = 1

        if current_section:
            if current_section == "Expanded Plot":
                # Logic says: "dupa Expanded Plot nu are sens", but maybe we just default to Chapter 1? 
                # Request says: "dupa Expanded Plot nu are sens". So we might return None or handle gracefully.
                # Let's assume UI prevents this, but if called, we treat as start (Fill 1).
                target_chapter_index = 1
            elif current_section == "Chapters Overview":
                # "dupa Chapters Overview e OK, inseamna ca se doreste adaugarea unui prim capitol ca fill" -> Fill 1 (#1)
                target_chapter_index = 1
            elif current_section.startswith("Chapter "):
                try:
                    # "dupa Chapter 2, atunci x e 3"
                    idx = int(current_section.split(" ")[1])
                    target_chapter_index = idx + 1
                except ValueError:
                    target_chapter_index = 1
            elif "Fill" in current_section:
                # "cand section selectat e alt fill ... eg, existau Fill 3 (#1) ... se va crea acum Fill 3 (#2)"
                # Name format: "Fill 3 (#1)"
                parts = current_section.split(" ")
                if len(parts) >= 3 and parts[0] == "Fill":
                    try:
                        target_chapter_index = int(parts[1])
                        # Parse (#Y)
                        y_part = parts[2].strip("(#)")
                        last_y = int(y_part)
                        fill_number = last_y + 1
                    except ValueError:
                        pass
        
        # Determine strict next available fill number if not derived from previous fill
        if "Fill" not in (current_section or ""):
            # Check existing fills for this target index to find next Y
            # We need to scan existing drafts to see if "Fill X (#?)" exists
            dm = DraftsManager()
            drafts = dm.get_all_draft_keys() # Helper needed? Or just iterate keys
            
            # Since DraftsManager doesn't expose keys easily, we might need a helper or just rely on logic
            # Actually DraftsManager.has() checks section existence.
            # We can try incrementing Y until we find a gap? No, we need to append.
            # "daca de ex se apasa de 2 ori pe butonul de fill ... se vor crea intai Fill 3 (#1) apoi Fill 3 (#2)"
            
            # This implies we blindly create #1? No, if #1 exists we make #2.
            # We need a way to list drafts from DraftsManager.
            # Let's add `get_all_sections()` to DraftsManager or check iteratively.
            # Iterating is safer.
            y = 1
            while True:
                candidate = f"Fill {target_chapter_index} (#{y})"
                if dm.has(candidate):
                    y += 1
                else:
                    fill_number = y
                    break

        new_fill_name = f"Fill {target_chapter_index} (#{fill_number})"
        
        # Create empty draft
        DraftsManager().add_fill_draft(new_fill_name, "")
        
        return new_fill_name

    def is_fill(self, section_name: str) -> bool:
        """Check if section has a FILL draft type in DraftsManager."""
        if not section_name:
            return False
        drafts_mgr = DraftsManager()
        return drafts_mgr.has_type(section_name, DraftType.FILL.value)

    def parse_fill_target(self, section_name: str) -> Optional[int]:
        """Returns target chapter index X from 'Fill X (#Y)' if name matches pattern."""
        if not section_name or not section_name.startswith("Fill ") or "(#" not in section_name:
            return None
        try:
            parts = section_name.split(" ")
            return int(parts[1])
        except (IndexError, ValueError):
            return None
    
    def shift_fills_after_insert(self, inserted_chapter_index: int, removed_fill_name: str) -> None:
        """
        When a chapter is inserted at index, shift all fills with target >= index.
        The fill that was converted to chapter is already removed.
        Fills are shifted: Fill X -> Fill X+1, with Y reset to 1 and incremented if needed.
        Moves ALL drafts associated with each fill section (FILL, USER, CHAT, GENERATED, ORIGINAL).
        Also shifts all existing chapters with index >= inserted_chapter_index.
        """
        drafts_mgr = DraftsManager()
        all_fills = drafts_mgr.get_fill_drafts()
        
        def get_fill_sort_key(name):
            target = self.parse_fill_target(name)
            if target is None:
                return (9999, 9999)
            try:
                parts = name.split(" ")
                y = int(parts[2].strip("(#)"))
                return (target, y)
            except:
                return (target, 9999)
        
        all_fills.sort(key=get_fill_sort_key, reverse=True)
        
        for fill_name in all_fills:
            fill_target = self.parse_fill_target(fill_name)
            if fill_target is not None and fill_target >= inserted_chapter_index:
                new_target = fill_target + 1
                
                y_part = 1
                new_fill_name = f"Fill {new_target} (#{y_part})"
                
                while drafts_mgr.has(new_fill_name):
                    y_part += 1
                    new_fill_name = f"Fill {new_target} (#{y_part})"
                
                drafts_mgr.move_all_drafts(fill_name, new_fill_name)
        
        drafts_mgr.shift_chapters_after_insert(inserted_chapter_index)