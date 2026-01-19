from typing import Dict

PROVIDER_CAPABILITIES: Dict[str, Dict[str, bool]] = {
    "Automatic1111": {"has_url": True, "has_api_key": False, "has_reasoning": False},
    "DeepSeek": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "Gemini": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "LM Studio": {"has_url": True, "has_api_key": False, "has_reasoning": True},
    "Moonshot": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "OpenAI": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "OpenRouter": {"has_url": False, "has_api_key": True, "has_reasoning": True},
    "xAI": {"has_url": False, "has_api_key": True, "has_reasoning": True}
}

