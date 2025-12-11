from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

def generate_text(settings: Dict[str, Any], messages: List[Dict[str, str]], **kwargs) -> str:
    api_key = settings.get("api_key")
    if not api_key:
        raise ValueError("Gemini API Key is missing.")
        
    model = settings.get("technical_name") or "gemini-pro"
    reasoning = settings.get("reasoning", False)
    
    try:
        llm_params = {
            "google_api_key": api_key,
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 4000),
            "timeout": kwargs.get("timeout", 60)
        }
        
        if reasoning:
            llm_params["reasoning_effort"] = "minimal"
        
        llm = ChatGoogleGenerativeAI(**llm_params)
        
        lc_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))
                
        response = llm.invoke(lc_messages)
        return response.content
        
    except Exception as e:
        raise Exception(f"Gemini Text Error (LangChain): {e}")

