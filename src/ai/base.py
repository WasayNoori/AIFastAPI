from abc import ABC, abstractmethod

class AIPlatform(ABC):
    @abstractmethod
    def chat(self,prompt:str)->str:
        """sends a prompt to the ai and returns the response"""
        pass
    
    @abstractmethod
    def generate_image(self,prompt:str)->str:
        """sends a prompt to the ai and returns the image"""
        pass
    
    @abstractmethod
    def generate_text(self,prompt:str)->str:
        """sends a prompt to the ai and returns generated text"""
        pass