from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List

class LLMTaskName(Enum):
    CHAPTER_EDITOR = "chapter_editor"
    CHAPTER_SUMMARY = "chapter_summary"
    CHAPTER_VALIDATOR = "chapter_validator"
    CHAPTER_WRITER = "chapter_writer"
    CHAT_EDITOR = "chat_editor"
    CHAT_FILLER = "chat_filler"
    CHAT_REFINER = "chat_refiner"
    COVER_PROMPTER = "cover_prompter"
    IMPACT_ANALYZER = "impact_analyzer"
    OVERVIEW_EDITOR = "overview_editor"
    OVERVIEW_GENERATOR = "overview_generator"
    OVERVIEW_GENERATOR_FROM_FILL = "overview_generator_from_fill"
    OVERVIEW_VALIDATOR = "overview_validator"
    OVERVIEW_VALIDATOR_AFTER_EDIT = "overview_validator_after_edit"
    PLOT_EDITOR = "plot_editor"
    PLOT_EXPANDER = "plot_expander"
    PLOT_GENERATOR_FROM_FILL = "plot_generator_from_fill"
    REFINE_CHAT = "refine_chat"
    REFINE_PLOT = "refine_plot"
    REWRITE_EDITOR = "rewrite_editor"
    TITLE_FETCHER = "title_fetcher"
    VERSION_DIFF = "version_diff"


@dataclass
class TaskDefaults:
    technical_name: str
    display_name: str
    max_tokens: int
    timeout: int
    temperature: float
    top_p: float


REASONING_EFFORT_OPTIONS = [
    "Not Set",
    "Very High",
    "High",
    "Medium",
    "Low",
    "Minimal",
    "None"
]


LLM_TASK_DEFAULTS: Dict[LLMTaskName, TaskDefaults] = {
    LLMTaskName.CHAPTER_EDITOR: TaskDefaults(
        "chapter_editor", "Chapter Editor", 16000, 3600, 0.8, 0.95
    ),
    LLMTaskName.CHAPTER_SUMMARY: TaskDefaults(
        "chapter_summary", "Chapter Summary", 2000, 120, 0.3, 0.9
    ),
    LLMTaskName.CHAPTER_VALIDATOR: TaskDefaults(
        "chapter_validator", "Chapter Validator", 2000, 300, 0.3, 0.9
    ),
    LLMTaskName.CHAPTER_WRITER: TaskDefaults(
        "chapter_writer", "Chapter Writer", 16000, 3600, 0.8, 0.95
    ),
    LLMTaskName.CHAT_EDITOR: TaskDefaults(
        "chat_editor", "Chat Editor", 16000, 300, 0.8, 0.95
    ),
    LLMTaskName.CHAT_FILLER: TaskDefaults(
        "chat_filler", "Chat Filler", 16000, 300, 0.7, 0.95
    ),
    LLMTaskName.CHAT_REFINER: TaskDefaults(
        "chat_refiner", "Chat Refiner", 4000, 60, 0.8, 0.95
    ),
    LLMTaskName.COVER_PROMPTER: TaskDefaults(
        "cover_prompter", "Cover Prompter", 1000, 120, 0.7, 0.95
    ),
    LLMTaskName.IMPACT_ANALYZER: TaskDefaults(
        "impact_analyzer", "Impact Analyzer", 4000, 300, 0.1, 0.3
    ),
    LLMTaskName.OVERVIEW_EDITOR: TaskDefaults(
        "overview_editor", "Overview Editor", 16000, 300, 0.6, 0.95
    ),
    LLMTaskName.OVERVIEW_GENERATOR: TaskDefaults(
        "overview_generator", "Overview Generator", 32000, 3600, 0.6, 0.95
    ),
    LLMTaskName.OVERVIEW_GENERATOR_FROM_FILL: TaskDefaults(
        "overview_generator_from_fill", "Overview Generator From Fill", 4000, 300, 0.6, 0.95
    ),
    LLMTaskName.OVERVIEW_VALIDATOR: TaskDefaults(
        "overview_validator", "Overview Validator", 4000, 300, 0.6, 0.9
    ),
    LLMTaskName.OVERVIEW_VALIDATOR_AFTER_EDIT: TaskDefaults(
        "overview_validator_after_edit", "Overview Validator After Edit", 1000, 120, 0.1, 0.5
    ),
    LLMTaskName.PLOT_EDITOR: TaskDefaults(
        "plot_editor", "Plot Editor", 8192, 300, 0.7, 0.95
    ),
    LLMTaskName.PLOT_EXPANDER: TaskDefaults(
        "plot_expander", "Plot Expander", 8192, 300, 0.7, 0.95
    ),
    LLMTaskName.PLOT_GENERATOR_FROM_FILL: TaskDefaults(
        "plot_generator_from_fill", "Plot Generator From Fill", 4096, 300, 0.7, 0.95
    ),
    LLMTaskName.REFINE_CHAT: TaskDefaults(
        "refine_chat", "Refine Chat", 16000, 1800, 0.7, 0.95
    ),
    LLMTaskName.REFINE_PLOT: TaskDefaults(
        "refine_plot", "Refine Plot", 8000, 900, 0.8, 0.9
    ),
    LLMTaskName.REWRITE_EDITOR: TaskDefaults(
        "rewrite_editor", "Rewrite Editor", 4000, 300, 0.7, 0.95
    ),
    LLMTaskName.TITLE_FETCHER: TaskDefaults(
        "title_fetcher", "Title Fetcher", 500, 120, 0.7, 0.95
    ),
    LLMTaskName.VERSION_DIFF: TaskDefaults(
        "version_diff", "Version Diff", 4000, 300, 0.3, 0.9
    ),
}


def get_task_defaults(task_name: str) -> Optional[TaskDefaults]:
    """Get defaults for a task by technical name string."""
    for enum_val, defaults in LLM_TASK_DEFAULTS.items():
        if defaults.technical_name == task_name:
            return defaults
    return None


def get_all_llm_tasks() -> List[Dict[str, str]]:
    """Get all LLM tasks as a list of dicts with technical_name and display_name."""
    return [
        {"technical_name": defaults.technical_name, "display_name": defaults.display_name}
        for defaults in LLM_TASK_DEFAULTS.values()
    ]


