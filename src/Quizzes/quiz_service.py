from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# Define Pydantic models for quiz structure
class QuizOption(BaseModel):
    text: str = Field(description="The text of the answer option")
    isCorrect: bool = Field(description="Whether this option is the correct answer")
    imageUrl: str = Field(default="", description="Optional image URL for the option")


class QuizQuestion(BaseModel):
    text: str = Field(description="The question text")
    category: str = Field(description="The category of the question")
    difficulty: int = Field(description="Difficulty level: 1=easy, 2=medium, 3=hard")
    productId: Optional[int] = Field(default=None, description="Product ID (null for default)")
    createdById: Optional[int] = Field(default=None, description="Creator ID (null for default)")
    imageUrl: str = Field(default="", description="Optional image URL for the question")
    tags: str = Field(description="Comma-separated tags for the question")
    languageId: int = Field(default=1, description="Language ID (1 for English)")
    options: List[QuizOption] = Field(description="List of exactly 4 answer options")


class QuizResult(BaseModel):
    questions: List[QuizQuestion] = Field(description="List of generated quiz questions")


class QuizGenerationService:
    """Service for generating quiz questions using LangChain and OpenAI LLM"""

    def __init__(self, azure_config):
        """
        Initialize the quiz generation service with OpenAI LLM

        Args:
            azure_config: Azure configuration to get OpenAI API key
        """
        try:
            # Get OpenAI API key from Azure Key Vault
            logger.info("Getting OpenAI API key from Azure Key Vault...")
            openai_api_key = azure_config.get_secret("OPENAI-KEY")

            if not openai_api_key:
                raise ValueError("OPENAI-KEY not found in Azure Key Vault")

            # Initialize OpenAI LLM
            logger.info("Initializing OpenAI LLM...")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=openai_api_key,
                temperature=0.7,
                max_tokens=4096
            )

            # Initialize output parser
            self.parser = JsonOutputParser(pydantic_object=QuizResult)

            # Load the quiz template
            template_path = Path("src/Quizzes/prompts/QuizTemplate.txt")
            if not template_path.exists():
                raise FileNotFoundError(f"Quiz template not found at {template_path}")

            self.quiz_template = template_path.read_text()

            logger.info("QuizGenerationService initialized successfully")

        except FileNotFoundError as e:
            logger.error(f"Template file error: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize QuizGenerationService: {str(e)}", exc_info=True)
            raise

    def generate_quiz(self, source_text: str) -> QuizResult:
        """
        Generate quiz questions from the provided text

        Args:
            source_text: The text to generate quiz questions from

        Returns:
            QuizResult containing a list of generated questions
        """
        try:
            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.quiz_template),
                ("human", "Source Text:\n{source_text}\n\n{format_instructions}")
            ])

            # Create the chain
            chain = prompt | self.llm | self.parser

            # Generate the quiz
            result = chain.invoke({
                "source_text": source_text,
                "format_instructions": self.parser.get_format_instructions()
            })

            # Parse the result into QuizResult
            quiz_result = QuizResult(**result)

            logger.info(f"Successfully generated {len(quiz_result.questions)} quiz questions")

            return quiz_result

        except Exception as e:
            logger.error(f"Failed to generate quiz: {str(e)}")
            raise
