# pipeline/pipeline_context.py
from dataclasses import dataclass, field
from typing import List, Optional
from pipeline.constants import RUN_MODE_CHOICES

@dataclass
class PipelineContext:
    plot: str = ""
    expanded_plot: Optional[str] = None
    chapters_overview: Optional[str] = None
    chapters_full: List[str] = field(default_factory=list)
    validation_text: str = ""
    status_log: List[str] = field(default_factory=list)
    genre: str = ""
    anpc: int = 0
    num_chapters: int = 0
    run_mode: str = RUN_MODE_CHOICES["FULL"]
    overview_validated: bool = False
    choices: Optional[List[str]] = None
    next_chapter_index: Optional[int] = None
    pending_validation_index: Optional[int] = None

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_checkpoint(cls, checkpoint: dict):
        data = checkpoint.copy()
        if "chapters_full" in data and isinstance(data["chapters_full"], list):
            data["chapters_full"] = list(data["chapters_full"])
        if "status_log" in data and isinstance(data["status_log"], list):
            data["status_log"] = list(data["status_log"])
        return cls(**data)

