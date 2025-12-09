# llm/cover_prompter/llm.py
import textwrap
from provider import provider_manager

def generate_prompt(story_context: str,
                    api_url: str = None,
                    model_name: str = None,
                    timeout: int = 300) -> str:
    """
    Generates a Stable Diffusion prompt for a book cover based on the story context.
    
    Args:
        story_context: The expanded plot or story summary.
        api_url: Optional API URL override.
        model_name: Optional model name override.
        timeout: Request timeout in seconds.
        
    Returns:
        A string containing the generated prompt.
    """
    if not story_context:
        return ""

    system_prompt = """
    You are an Expert Book Cover Artist and Prompt Engineer.
    Your task is to create a high-quality Stable Diffusion prompt for a book cover based on the provided story context.
    
    Constraints:
    1. **No Spoilers**: Focus on the setting, atmosphere, characters in general (not necessarily main), places, abstract themes, or important objects in the book. Do NOT depict plot twists or ending events.
    2. **Style**: High quality, detailed, trending on artstation, 8k, cinematic lighting, photorealistic or digital art style appropriate for the genre.
    3. **Format**: Return ONLY the prompt text. Do not include explanations or labels like "Prompt:".
    
    The prompt should be descriptive and comma-separated, focusing on visual elements.
    Example: "A dark forest with glowing mushrooms, a mysterious hooded figure standing in the shadows, magical atmosphere, 8k, detailed, fantasy art style"
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Story Context:\n{story_context}"}
    ]
    
    try:
        content = provider_manager.get_llm_response(
            task_name="cover_prompter",
            messages=messages,
            timeout=timeout,
            temperature=0.7,
            max_tokens=150
        )
        # Cleanup
        content = content.replace('"', '').replace("Prompt:", "").strip()
        return content
    except Exception as e:
        return f"Error generating prompt: {e}"

