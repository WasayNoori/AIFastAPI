from langchain.llms import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.llms import BaseLLM
import os
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LangChainService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        self.chat_model = GoogleGenerativeAI(model="gemini-1.5-flash", api_key=api_key)
        
        self.summarize_prompt = PromptTemplate(
            input_variables=["text"],
            template="""
            Please summarize the following text in a clear, concise paragraph of no more than 100 words. 
            Focus on the key points and main ideas:

            Text: {text}

            Summary:
            """
        )
    
    async def summarize_text(self, text_content: str) -> str:
        """
        Summarize the given text content in a paragraph of no more than 100 words.
        
        Args:
            text_content (str): The text content to summarize
            
        Returns:
            str: A concise summary of the text
        """
        try:
            logger.info(f"Summarizing text content ({len(text_content)} characters)")
            
            # Format the prompt with the text content
            formatted_prompt = self.summarize_prompt.format(text=text_content)
            
            # Run the LLM call in a thread pool to make it async
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None, 
                self.chat_model, 
                formatted_prompt
            )
            
            logger.info("Text summarization completed successfully")
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Failed to summarize text: {str(e)}")
            raise

