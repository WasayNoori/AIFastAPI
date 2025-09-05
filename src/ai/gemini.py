from .base import AIPlatform

class Gemini(AIPlatform):
    def __init__(self, api_key: str,system_prompt:str=None):
        self.api_key = api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=api_key)
    
    def chat(self, prompt: str) -> str:
        # Implement Gemini chat functionality
        pass
    
    def generate_image(self, prompt: str) -> str:
        # Implement Gemini image generation functionality
        pass
    
    def generate_text(self, prompt: str) -> str:
        # Implement Gemini text generation functionality
        pass