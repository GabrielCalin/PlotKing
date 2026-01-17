
from typing import List, Dict, Any, Optional
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
    """
    model_settings = settings_manager.get_model_for_task(task_name)
    if not model_settings:
        # Fallback to default if not assigned (though settings_manager handles defaulting usually)
        # Getting default manually if something failed
        defaults = [m for m in settings_manager.get_models() if m.get("name") == "default_llm"]
        if defaults:
            model_settings = defaults[0]
        else:
            raise Exception(f"No model configured for task '{task_name}' and no default found.")
            
    provider = model_settings.get("provider")
    
    if provider == "LM Studio":
        return lm_studio.generate_text(model_settings, messages, **kwargs)
    elif provider == "OpenAI":
        return openai_provider.generate_text(model_settings, messages, **kwargs)
    elif provider == "Gemini":
        return gemini_provider.generate_text(model_settings, messages, **kwargs)
    elif provider == "xAI":
        return xai_provider.generate_text(model_settings, messages, **kwargs)
    elif provider == "DeepSeek":
        return deepseek_provider.generate_text(model_settings, messages, **kwargs)
    elif provider == "OpenRouter":
        return openrouter_provider.generate_text(model_settings, messages, **kwargs)
    elif provider == "Moonshot":
        return moonshot_provider.generate_text(model_settings, messages, **kwargs)
    else:
        raise Exception(f"Unknown or unsupported LLM provider: {provider}")

def generate_image(task_name: str, prompt: str, **kwargs) -> str:
    """
    Generic entry point for Image tasks. Returns absolute path to generated image.
    """
    model_settings = settings_manager.get_model_for_task(task_name)
    if not model_settings:
        defaults = [m for m in settings_manager.get_models() if m.get("name") == "default_image"]
        if defaults:
            model_settings = defaults[0]
        else:
            raise Exception(f"No model configured for task '{task_name}' and no default image model found.")
            
    provider = model_settings.get("provider")
    
    if provider == "Automatic1111":
        return automatic1111.generate_image(model_settings, prompt, **kwargs)
    elif provider == "OpenAI":
        return openai_provider.generate_image(model_settings, prompt, **kwargs)
    else:
        raise Exception(f"Unknown or unsupported Image provider: {provider}")
