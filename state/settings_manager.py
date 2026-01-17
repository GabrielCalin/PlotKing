
import os
import json
from typing import List, Dict, Any, Optional

SETTINGS_FILE = os.path.join("settings", "settings.json")

# Default Models
DEFAULT_LLM_MODEL = {
    "name": "default_llm",
    "id": "default_llm",  # Using name as ID for simplicity if unique, or we can enforce uniqueness
    "technical_name": "",
    "type": "llm",
    "provider": "LM Studio",
    "url": "http://127.0.0.1:1234",
    "api_key": "",
    "is_default": True
}

DEFAULT_IMAGE_MODEL = {
    "name": "default_image",
    "id": "default_image",
    "technical_name": "",
    "type": "image",
    "provider": "Automatic1111",
    "url": "http://127.0.0.1:7860", # Standard A1111 port is 7860 usually, but user said 6969 in request? checking request... user said 6969.
    "api_key": "",
    "is_default": True
}
# Correction based on user request:
# "URL http://127.0.0.1:6969" for default_image.

DEFAULT_IMAGE_MODEL["url"] = "http://127.0.0.1:6969"

PROVIDER_CAPABILITIES = {
    "OpenAI": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "Gemini": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "xAI": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "DeepSeek": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "OpenRouter": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "Moonshot": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "LM Studio": {"has_url": True, "has_api_key": False, "has_reasoning": False},
    "Automatic1111": {"has_url": True, "has_api_key": False, "has_reasoning": False}
}

LLM_PROVIDERS = ["LM Studio", "OpenAI", "Gemini", "xAI", "DeepSeek", "OpenRouter", "Moonshot"]
IMAGE_PROVIDERS = ["Automatic1111", "OpenAI"]


# Known Tasks (Hardcoded list + dynamic scan could be better, but user said "sa fie toate")
# We will define them here.
LLM_TASKS = [
    {"technical_name": "chapter_editor", "display_name": "Chapter Editor"},
    {"technical_name": "chapter_summary", "display_name": "Chapter Summary"},
    {"technical_name": "chapter_validator", "display_name": "Chapter Validator"},
    {"technical_name": "chapter_writer", "display_name": "Chapter Writer"},
    {"technical_name": "chat_editor", "display_name": "Chat Editor"},
    {"technical_name": "chat_filler", "display_name": "Chat Filler"},
    {"technical_name": "chat_refiner", "display_name": "Chat Refiner"},
    {"technical_name": "cover_prompter", "display_name": "Cover Prompter"},
    {"technical_name": "impact_analyzer", "display_name": "Impact Analyzer"},
    {"technical_name": "overview_editor", "display_name": "Overview Editor"},
    {"technical_name": "overview_generator", "display_name": "Overview Generator"},
    {"technical_name": "overview_generator_from_fill", "display_name": "Overview Generator From Fill"},
    {"technical_name": "overview_validator", "display_name": "Overview Validator"},
    {"technical_name": "overview_validator_after_edit", "display_name": "Overview Validator After Edit"},
    {"technical_name": "plot_editor", "display_name": "Plot Editor"},
    {"technical_name": "plot_expander", "display_name": "Plot Expander"},
    {"technical_name": "plot_generator_from_fill", "display_name": "Plot Generator From Fill"},
    {"technical_name": "refine_chat", "display_name": "Refine Chat"},
    {"technical_name": "refine_plot", "display_name": "Refine Plot"},
    {"technical_name": "rewrite_editor", "display_name": "Rewrite Editor"},
    {"technical_name": "title_fetcher", "display_name": "Title Fetcher"},
    {"technical_name": "version_diff", "display_name": "Version Diff"}
]

IMAGE_TASKS = [
    {"technical_name": "cover_image_generation", "display_name": "Cover Image Generation"}
]

class SettingsManager:
    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        if not os.path.exists("settings"):
            os.makedirs("settings")
            
        if not os.path.exists(SETTINGS_FILE):
            return self._create_default_settings()
            
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return self._validate_and_fix_settings(settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Backup corrupt file if it exists so we don't lose data on next save
            if os.path.exists(SETTINGS_FILE):
                 import shutil
                 backup_path = SETTINGS_FILE + ".bak"
                 try:
                     shutil.copy2(SETTINGS_FILE, backup_path)
                     print(f"Corrupt settings backed up to {backup_path}")
                 except Exception as backup_err:
                     print(f"Failed to backup corrupt settings: {backup_err}")
            
            return self._create_default_settings()

    def _create_default_settings(self) -> Dict[str, Any]:
        settings = {
            "models": [DEFAULT_LLM_MODEL.copy(), DEFAULT_IMAGE_MODEL.copy()],
            "tasks": {}
        }
        
        # Assign defaults to tasks
        for task in LLM_TASKS:
            settings["tasks"][task["technical_name"]] = "default_llm"
            
        for task in IMAGE_TASKS:
            settings["tasks"][task["technical_name"]] = "default_image"
            
        return settings

    def _validate_and_fix_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required fields/defaults exist even in loaded settings."""
        if "models" not in settings:
            settings["models"] = []
            
        # Ensure default models exist
        model_names = {m["name"] for m in settings["models"]}
        if "default_llm" not in model_names:
            settings["models"].append(DEFAULT_LLM_MODEL.copy())
        if "default_image" not in model_names:
            settings["models"].append(DEFAULT_IMAGE_MODEL.copy())
            
        if "tasks" not in settings:
            settings["tasks"] = {}
            
        # Ensure all tasks have an assignment
        current_models = {m["name"]: m for m in settings["models"]}
        
        for task in LLM_TASKS:
            tech_name = task["technical_name"]
            if tech_name not in settings["tasks"] or settings["tasks"][tech_name] not in current_models:
               settings["tasks"][tech_name] = "default_llm"

        for task in IMAGE_TASKS:
            tech_name = task["technical_name"]
            if tech_name not in settings["tasks"] or settings["tasks"][tech_name] not in current_models:
                settings["tasks"][tech_name] = "default_image"
                
        return settings

    def save_settings(self, new_settings: Dict[str, Any] = None):
        if new_settings:
            self.settings = self._validate_and_fix_settings(new_settings)
            
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def get_models(self) -> List[Dict[str, Any]]:
        return self.settings["models"]

    def get_tasks(self) -> Dict[str, str]:
        return self.settings["tasks"]
    
    def get_model_for_task(self, task_name: str) -> Optional[Dict[str, Any]]:
        model_name = self.settings["tasks"].get(task_name)
        if not model_name:
            return None
        
        for model in self.settings["models"]:
            if model["name"] == model_name:
                return model
        return None

    def add_model(self, model: Dict[str, Any]):
        # Check name uniqueness
        if any(m["name"] == model["name"] for m in self.settings["models"]):
            raise ValueError(f"Model with name '{model['name']}' already exists.")
        self.settings["models"].append(model)
        self.save_settings()
        
    def update_model(self, original_name: str, updated_model: Dict[str, Any]):
        for i, model in enumerate(self.settings["models"]):
            if model["name"] == original_name:
                # If name changed, update tasks using this model
                if original_name != updated_model["name"]:
                     self._update_task_assignments_on_rename(original_name, updated_model["name"])
                
                self.settings["models"][i] = updated_model
                self.save_settings()
                return
        raise ValueError(f"Model '{original_name}' not found.")

    def delete_model(self, model_name: str):
        # Prevent deleting defaults
        if model_name in ["default_llm", "default_image"]:
            raise ValueError("Cannot delete default models.")
            
        model_to_delete = None
        for model in self.settings["models"]:
            if model["name"] == model_name:
                model_to_delete = model
                break
        
        if not model_to_delete:
            raise ValueError(f"Model '{model_name}' not found.")
            
        self.settings["models"].remove(model_to_delete)
        
        # Reassign tasks using this model to default
        model_type = model_to_delete.get("type", "llm")
        fallback_model = "default_llm" if model_type == "llm" else "default_image"
        
        for task, assigned_model in self.settings["tasks"].items():
            if assigned_model == model_name:
                self.settings["tasks"][task] = fallback_model
                # logging this action could be good, but we usually log to UI. 
                # We'll handle UI logging in the UI layer.

        self.save_settings()

    def get_provider_capabilities(self, provider_name: str) -> Dict[str, bool]:
        # Default to URL only if unknown, or safe fallback
        return PROVIDER_CAPABILITIES.get(provider_name, {"has_url": True, "has_api_key": True})

    def _update_task_assignments_on_rename(self, old_name: str, new_name: str):
        for task, assigned_model in self.settings["tasks"].items():
            if assigned_model == old_name:
                self.settings["tasks"][task] = new_name

settings_manager = SettingsManager()
