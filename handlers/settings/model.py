from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class Model:
    name: str
    id: str
    technical_name: str
    type: str
    provider: str
    url: str
    api_key: str
    reasoning: bool = False
    is_default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Model":
        """Create Model from dictionary (for backwards compatibility)."""
        return cls(
            name=data.get("name", ""),
            id=data.get("id", data.get("name", "")),
            technical_name=data.get("technical_name", ""),
            type=data.get("type", "llm"),
            provider=data.get("provider", ""),
            url=data.get("url", ""),
            api_key=data.get("api_key", ""),
            reasoning=data.get("reasoning", False),
            is_default=data.get("is_default", False)
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for backwards compatibility."""
        return getattr(self, key, default)


DEFAULT_LLM_MODEL = Model(
    name="default_llm",
    id="default_llm",
    technical_name="",
    type="llm",
    provider="LM Studio",
    url="http://127.0.0.1:1234",
    api_key="",
    is_default=True
)

DEFAULT_IMAGE_MODEL = Model(
    name="default_image",
    id="default_image",
    technical_name="",
    type="image",
    provider="Automatic1111",
    url="http://127.0.0.1:6969",
    api_key="",
    is_default=True
)

LLM_PROVIDERS: List[str] = ["LM Studio", "OpenAI", "Gemini", "xAI", "DeepSeek", "OpenRouter", "Moonshot"]
IMAGE_PROVIDERS: List[str] = ["Automatic1111", "OpenAI"]
