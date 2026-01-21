
import os
import json
from typing import List, Dict, Any, Optional, Union

from handlers.settings import (
    get_all_llm_tasks,
    get_task_defaults,
    IMAGE_TASKS,
    DEFAULT_LLM_MODEL,
    DEFAULT_IMAGE_MODEL,
    PROVIDER_CAPABILITIES,
    Model
)

SETTINGS_FILE = os.path.join("settings", "settings.json")

LLM_TASKS = get_all_llm_tasks()


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
            if os.path.exists(SETTINGS_FILE):
                 import shutil
                 backup_path = SETTINGS_FILE + ".bak"
                 try:
                     shutil.copy2(SETTINGS_FILE, backup_path)
                     print(f"Corrupt settings backed up to {backup_path}")
                 except Exception as backup_err:
                     print(f"Failed to backup corrupt settings: {backup_err}")
            
            return self._create_default_settings()

    def _create_task_settings(self, model_name: str, task_name: str) -> Dict[str, Any]:
        """Create task settings dict with defaults from the task definition."""
        defaults = get_task_defaults(task_name)
        if defaults:
            return {
                "model": model_name,
                "max_tokens": defaults.max_tokens,
                "timeout": defaults.timeout,
                "temperature": defaults.temperature,
                "top_p": defaults.top_p,
                "retries": defaults.retries,
                "reasoning_effort": None,
                "max_reasoning_tokens": None
            }
        return {
            "model": model_name,
            "max_tokens": 4000,
            "timeout": 300,
            "temperature": 0.7,
            "top_p": 0.95,
            "retries": 3,
            "reasoning_effort": None,
            "max_reasoning_tokens": None
        }

    def _create_default_settings(self) -> Dict[str, Any]:
        settings = {
            "models": [DEFAULT_LLM_MODEL, DEFAULT_IMAGE_MODEL],
            "tasks": {}
        }
        
        for task in LLM_TASKS:
            tech_name = task["technical_name"]
            settings["tasks"][tech_name] = self._create_task_settings("default_llm", tech_name)
            
        for task in IMAGE_TASKS:
            settings["tasks"][task["technical_name"]] = {"model": "default_image"}
            
        return settings

    def _validate_and_fix_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required fields/defaults exist. Converts dicts to Model objects."""
        if "models" not in settings:
            settings["models"] = []
        
        models_list = []
        for m in settings["models"]:
            if isinstance(m, dict):
                models_list.append(Model.from_dict(m))
            elif isinstance(m, Model):
                models_list.append(m)
            else:
                models_list.append(m)
        
        model_names = {m.name for m in models_list if isinstance(m, Model)} | {m["name"] for m in models_list if isinstance(m, dict)}
        if "default_llm" not in model_names:
            models_list.append(DEFAULT_LLM_MODEL)
        if "default_image" not in model_names:
            models_list.append(DEFAULT_IMAGE_MODEL)
        
        settings["models"] = models_list
        
        if "tasks" not in settings:
            settings["tasks"] = {}
            
        current_models = {}
        for m in models_list:
            if isinstance(m, Model):
                current_models[m.name] = m
            elif isinstance(m, dict):
                current_models[m["name"]] = m
        
        for task in LLM_TASKS:
            tech_name = task["technical_name"]
            task_value = settings["tasks"].get(tech_name)
            
            if task_value is None:
                settings["tasks"][tech_name] = self._create_task_settings("default_llm", tech_name)
            elif isinstance(task_value, dict):
                model_name = task_value.get("model", "default_llm")
                if model_name not in current_models:
                    task_value["model"] = "default_llm"
                defaults = get_task_defaults(tech_name)
                if defaults:
                    if "max_tokens" not in task_value:
                        task_value["max_tokens"] = defaults.max_tokens
                    if "timeout" not in task_value:
                        task_value["timeout"] = defaults.timeout
                    if "temperature" not in task_value:
                        task_value["temperature"] = defaults.temperature
                    if "top_p" not in task_value:
                        task_value["top_p"] = defaults.top_p
                    if "retries" not in task_value:
                        task_value["retries"] = defaults.retries
                else:
                    if "retries" not in task_value:
                        task_value["retries"] = 3
                if "reasoning_effort" not in task_value:
                    task_value["reasoning_effort"] = None
                if "max_reasoning_tokens" not in task_value:
                    task_value["max_reasoning_tokens"] = None

        for task in IMAGE_TASKS:
            tech_name = task["technical_name"]
            task_value = settings["tasks"].get(tech_name)
            if task_value is None:
                settings["tasks"][tech_name] = {"model": "default_image"}
            elif isinstance(task_value, dict):
                # Validate the model name
                model_name = task_value.get("model", "default_image")
                if model_name not in current_models:
                    task_value["model"] = "default_image"
            else:
                # Invalid format - convert to dict structure
                settings["tasks"][tech_name] = {"model": "default_image"}
                
        return settings

    def save_settings(self, new_settings: Dict[str, Any] = None):
        if new_settings:
            self.settings = self._validate_and_fix_settings(new_settings)
        
        models_for_json = []
        for m in self.settings["models"]:
            if isinstance(m, Model):
                models_for_json.append(m.to_dict())
            else:
                models_for_json.append(m)
        
        settings_for_json = {**self.settings, "models": models_for_json}
            
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings_for_json, f, indent=4)

    def get_models(self) -> List[Model]:
        """Get models as Model objects."""
        return [m if isinstance(m, Model) else Model.from_dict(m) for m in self.settings["models"]]

    def get_tasks(self) -> Dict[str, Any]:
        return self.settings["tasks"]
    
    def get_task_settings(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get full task settings including model and parameters."""
        task_data = self.settings["tasks"].get(task_name)
        if task_data is None:
            return None
        return task_data
    
    def get_model_for_task(self, task_name: str) -> Optional[Model]:
        """Get the model configuration for a task as Model object."""
        task_data = self.settings["tasks"].get(task_name)
        if not task_data or not isinstance(task_data, dict):
            return None
        
        model_name = task_data.get("model")
        if not model_name:
            return None
        
        for model in self.settings["models"]:
            model_obj = model if isinstance(model, Model) else Model.from_dict(model)
            if model_obj.name == model_name:
                return model_obj
        return None
    
    def get_task_params(self, task_name: str) -> Dict[str, Any]:
        """Get task parameters (max_tokens, timeout, temperature, top_p, retries, reasoning params)."""
        task_data = self.settings["tasks"].get(task_name)
        defaults = get_task_defaults(task_name)
        
        if task_data is None or not isinstance(task_data, dict):
            if defaults:
                return {
                    "max_tokens": defaults.max_tokens,
                    "timeout": defaults.timeout,
                    "temperature": defaults.temperature,
                    "top_p": defaults.top_p,
                    "retries": defaults.retries,
                    "reasoning_effort": None,
                    "max_reasoning_tokens": None
                }
            return {
                "max_tokens": 4000,
                "timeout": 300,
                "temperature": 0.7,
                "top_p": 0.95,
                "retries": 3,
                "reasoning_effort": None,
                "max_reasoning_tokens": None
            }
        
        result = {
            "max_tokens": task_data.get("max_tokens"),
            "timeout": task_data.get("timeout"),
            "temperature": task_data.get("temperature"),
            "top_p": task_data.get("top_p"),
            "retries": task_data.get("retries"),
            "reasoning_effort": task_data.get("reasoning_effort"),
            "max_reasoning_tokens": task_data.get("max_reasoning_tokens")
        }
        
        if defaults:
            if result["max_tokens"] is None:
                result["max_tokens"] = defaults.max_tokens
            if result["timeout"] is None:
                result["timeout"] = defaults.timeout
            if result["temperature"] is None:
                result["temperature"] = defaults.temperature
            if result["top_p"] is None:
                result["top_p"] = defaults.top_p
            if result["retries"] is None:
                result["retries"] = defaults.retries
        
        return result
    
    def update_task_settings(self, task_name: str, settings_update: Dict[str, Any]):
        """Update task settings (model and/or parameters)."""
        current = self.settings["tasks"].get(task_name)
        
        if current is None or not isinstance(current, dict):
            current = self._create_task_settings("default_llm", task_name)
        
        for key, value in settings_update.items():
            current[key] = value
        
        self.settings["tasks"][task_name] = current
        self.save_settings()

    def add_model(self, model: Dict[str, Any]):
        """Add a model. Accepts dict but stores as Model object."""
        model_obj = Model.from_dict(model) if isinstance(model, dict) else model
        if any(m.name == model_obj.name for m in self.settings["models"] if isinstance(m, Model)):
            raise ValueError(f"Model with name '{model_obj.name}' already exists.")
        self.settings["models"].append(model_obj)
        self.save_settings()
        
    def update_model(self, original_name: str, updated_model: Dict[str, Any]):
        """Update a model. Accepts dict but stores as Model object."""
        updated_obj = Model.from_dict(updated_model) if isinstance(updated_model, dict) else updated_model
        for i, model in enumerate(self.settings["models"]):
            model_name = model.name if isinstance(model, Model) else model["name"]
            if model_name == original_name:
                if original_name != updated_obj.name:
                     self._update_task_assignments_on_rename(original_name, updated_obj.name)
                
                self.settings["models"][i] = updated_obj
                self.save_settings()
                return
        raise ValueError(f"Model '{original_name}' not found.")

    def delete_model(self, model_name: str):
        if model_name in ["default_llm", "default_image"]:
            raise ValueError("Cannot delete default models.")
            
        model_to_delete = None
        for model in self.settings["models"]:
            current_name = model.name if isinstance(model, Model) else model["name"]
            if current_name == model_name:
                model_to_delete = model
                break
        
        if not model_to_delete:
            raise ValueError(f"Model '{model_name}' not found.")
            
        self.settings["models"].remove(model_to_delete)
        
        model_type = model_to_delete.type if isinstance(model_to_delete, Model) else model_to_delete.get("type", "llm")
        fallback_model = "default_llm" if model_type == "llm" else "default_image"
        
        for task_name, task_data in self.settings["tasks"].items():
            if isinstance(task_data, dict):
                if task_data.get("model") == model_name:
                    task_data["model"] = fallback_model

        self.save_settings()

    def get_provider_capabilities(self, provider_name: str) -> Dict[str, bool]:
        return PROVIDER_CAPABILITIES.get(provider_name, {"has_url": True, "has_api_key": True, "has_reasoning": False})

    def _update_task_assignments_on_rename(self, old_name: str, new_name: str):
        for task_name, task_data in self.settings["tasks"].items():
            if isinstance(task_data, dict):
                if task_data.get("model") == old_name:
                    task_data["model"] = new_name


settings_manager = SettingsManager()
