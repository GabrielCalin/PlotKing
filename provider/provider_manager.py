
from typing import List, Dict, Any
from state.settings_manager import settings_manager
import provider.lm_studio as lm_studio
import provider.automatic1111 as automatic1111
import provider.openai as openai_provider
import provider.gemini as gemini_provider
import provider.xai as xai_provider
import provider.deepseek as deepseek_provider
import provider.openrouter as openrouter_provider
import provider.moonshot as moonshot_provider


def get_llm_response(task_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
    """
    Generic entry point for LLM tasks.
    Reads parameters from task settings and merges with any explicit kwargs.
    Implements retry logic for HTTP errors.
    """
    model_settings = settings_manager.get_model_for_task(task_name)
    if not model_settings:
        defaults = [m for m in settings_manager.get_models() if m.name == "default_llm"]
        if defaults:
            model_settings = defaults[0]
        else:
            raise Exception(f"No model configured for task '{task_name}' and no default found.")
    
    task_params = settings_manager.get_task_params(task_name)
    
    merged_params = {
        "temperature": task_params.get("temperature", 0.7),
        "top_p": task_params.get("top_p", 0.95),
        "max_tokens": task_params.get("max_tokens", 4000),
        "timeout": task_params.get("timeout", 300),
    }
    
    has_reasoning = model_settings.reasoning
    if has_reasoning:
        reasoning_effort = task_params.get("reasoning_effort")
        if reasoning_effort and reasoning_effort not in ("None", "Not Set"):
            merged_params["reasoning_effort"] = reasoning_effort
        
        max_reasoning = task_params.get("max_reasoning_tokens")
        if max_reasoning:
            merged_params["max_reasoning_tokens"] = max_reasoning
    
    for key, value in kwargs.items():
        if value is not None:
            merged_params[key] = value
    
    provider = model_settings.provider
    model_dict = model_settings.to_dict()
    
    retries = task_params.get("retries", 3)
    if retries is None:
        retries = 3
    retries = max(0, int(retries))
    
    last_error = None
    for attempt in range(retries + 1):
        try:
            if provider == "LM Studio":
                return lm_studio.generate_text(model_dict, messages, **merged_params)
            elif provider == "OpenAI":
                return openai_provider.generate_text(model_dict, messages, **merged_params)
            elif provider == "Gemini":
                return gemini_provider.generate_text(model_dict, messages, **merged_params)
            elif provider == "xAI":
                return xai_provider.generate_text(model_dict, messages, **merged_params)
            elif provider == "DeepSeek":
                return deepseek_provider.generate_text(model_dict, messages, **merged_params)
            elif provider == "OpenRouter":
                return openrouter_provider.generate_text(model_dict, messages, **merged_params)
            elif provider == "Moonshot":
                return moonshot_provider.generate_text(model_dict, messages, **merged_params)
            else:
                raise Exception(f"Unknown or unsupported LLM provider: {provider}")
        except Exception as e:
            last_error = e
            if attempt < retries:
                continue
            raise Exception(f"LLM request failed after {retries + 1} attempts. Last error: {last_error}")


def generate_image(task_name: str, prompt: str, **kwargs) -> str:
    """
    Generic entry point for Image tasks. Returns absolute path to generated image.
    """
    model_settings = settings_manager.get_model_for_task(task_name)
    if not model_settings:
        defaults = [m for m in settings_manager.get_models() if m.name == "default_image"]
        if defaults:
            model_settings = defaults[0]
        else:
            raise Exception(f"No model configured for task '{task_name}' and no default image model found.")
    
    provider = model_settings.provider
    
    model_dict = model_settings.to_dict()
    
    if provider == "Automatic1111":
        return automatic1111.generate_image(model_dict, prompt, **kwargs)
    elif provider == "OpenAI":
        return openai_provider.generate_image(model_dict, prompt, **kwargs)
    else:
        raise Exception(f"Unknown or unsupported Image provider: {provider}")
