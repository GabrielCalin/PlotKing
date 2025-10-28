# -*- coding: utf-8 -*-
from datetime import datetime


def ts_prefix(message: str) -> str:
    """Return message prefixed with current datetime up to milliseconds."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"[{timestamp}] {message}"


class PipelineState:
    def __init__(self, expanded_plot=None, chapters_overview=None, chapters_full=None,
                 validation_text="", status_log=None, next_chapter_index=None,
                 genre=None, anpc=None, plot=None, num_chapters=None, run_mode=None,
                 overview_validated=False, choices=None, pending_validation_index=None):
        self.expanded_plot = expanded_plot
        self.chapters_overview = chapters_overview
        self.chapters_full = chapters_full or []
        self.validation_text = validation_text or ""
        self.status_log = status_log or []
        self.next_chapter_index = next_chapter_index
        self.genre = genre
        self.anpc = anpc
        self.plot = plot
        self.num_chapters = num_chapters
        self.run_mode = run_mode
        self.overview_validated = overview_validated
        self.choices = choices
        self.pending_validation_index = pending_validation_index

    # Convenience methods
    def log(self, message: str):
        """Append a timestamped message to status_log."""
        self.status_log.append(ts_prefix(message))

    def to_dict(self):
        """Convert to serializable dictionary for checkpointing."""
        return {
            "expanded_plot": self.expanded_plot,
            "chapters_overview": self.chapters_overview,
            "chapters_full": self.chapters_full,
            "validation_text": self.validation_text,
            "status_log": self.status_log,
            "next_chapter_index": self.next_chapter_index,
            "genre": self.genre,
            "anpc": self.anpc,
            "plot": self.plot,
            "num_chapters": self.num_chapters,
            "run_mode": self.run_mode,
            "overview_validated": self.overview_validated,
            "pending_validation_index": self.pending_validation_index,
        }

    @classmethod
    def from_checkpoint(cls, checkpoint: dict):
        """Initialize PipelineState from a checkpoint dict."""
        return cls(**checkpoint)
