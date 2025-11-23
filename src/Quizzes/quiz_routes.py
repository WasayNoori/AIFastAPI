from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import httpx
from pathlib import Path
from src.auth.dependencies import get_current_app, get_quiz_service
from src.Quizzes.quiz_service import QuizGenerationService
from src.Quizzes.config import SETTINGS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quiz", tags=["quiz"])


class GenerateQuizRequest(BaseModel):
    text: str = Field(description="The source text to generate quiz questions from")


class GenerateAndPushQuizRequest(BaseModel):
    text: str = Field(description="The source text to generate quiz questions from")


class ReadAndPushQuizRequest(BaseModel):
    file_path: str = Field(description="Full path to the text file to read and generate quiz questions from")


class SendQuizRequest(BaseModel):
    text: str = Field(description="The source text to generate quiz questions from")
    external_api_url: str = Field(description="The external API endpoint to send the questions to")
    headers: Optional[dict] = Field(default=None, description="Optional headers for the external API call")


@router.post("/generate")
async def generate_quiz(
    request: GenerateQuizRequest,
    current_user=Depends(get_current_app),
    quiz_service: QuizGenerationService = Depends(get_quiz_service)
):
    """
    Generate quiz questions from provided text using Gemini LLM.

    Args:
        request: Contains the source text
        current_user: Authenticated user
        quiz_service: Quiz generation service

    Returns:
        List of generated quiz questions in the specified format
    """
    try:
        # Generate quiz questions
        result = quiz_service.generate_quiz(request.text)

        # Convert to response format
        questions_list = [question.model_dump() for question in result.questions]

        return {
            "status": "success",
            "question_count": len(questions_list),
            "questions": questions_list,
            "processed_by": current_user.get("sub", "unknown")
        }

    except ValueError as e:
        logger.error(f"Quiz validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz: {str(e)}"
        )


@router.post("/generate-and-push")
async def generate_and_push_quiz(
    request: GenerateAndPushQuizRequest,
    current_user=Depends(get_current_app),
    quiz_service: QuizGenerationService = Depends(get_quiz_service)
):
    """
    Generate quiz questions from provided text and push them to the configured external API.
    Uses the URL from QUIZ_EXTERNAL_API_URL environment variable or default config.

    Args:
        request: Contains the source text and optional headers
        current_user: Authenticated user
        quiz_service: Quiz generation service

    Returns:
        Generated questions and response from external API
    """
    try:
        # Step 1: Generate quiz questions
        result = quiz_service.generate_quiz(request.text)

        # Convert to list format
        questions_list = [question.model_dump() for question in result.questions]

        # Step 2: Send to configured external API
        async with httpx.AsyncClient(verify=False) as client:  # verify=False for localhost with self-signed cert
            headers = {"Content-Type": "application/json"}

            external_response = await client.post(
                SETTINGS.external_api_url,
                json=questions_list,  # Send questions array directly
                headers=headers,
                timeout=float(SETTINGS.external_api_timeout)
            )

            external_response.raise_for_status()

        return {
            "status": "success",
            "question_count": len(questions_list),
            "questions": questions_list,
            "external_api_url": SETTINGS.external_api_url,
            "external_api_response": {
                "status_code": external_response.status_code,
                "response": external_response.json() if external_response.text else None
            },
            "processed_by": current_user.get("sub", "unknown")
        }

    except httpx.HTTPError as e:
        logger.error(f"External API call failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to push questions to external API ({SETTINGS.external_api_url}): {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Quiz validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Quiz generation and push failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate and push quiz: {str(e)}"
        )


@router.post("/read-and-generate")
async def read_and_generate_quiz(
    request: ReadAndPushQuizRequest,
    current_user=Depends(get_current_app),
    quiz_service: QuizGenerationService = Depends(get_quiz_service)
):
    """
    DEBUG ENDPOINT: Read text from a local file and generate quiz questions WITHOUT pushing to external API.
    Use this to see what would be sent to the external API.

    Args:
        request: Contains the file path to read
        current_user: Authenticated user
        quiz_service: Quiz generation service

    Returns:
        Generated questions (without sending to external API)
    """
    try:
        # Step 1: Read the file
        file_path = Path(request.file_path)

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_path}"
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=400,
                detail=f"Path is not a file: {request.file_path}"
            )

        # Read the file content
        logger.info(f"Reading file: {file_path}")
        text_content = file_path.read_text(encoding='utf-8')

        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail=f"File is empty: {request.file_path}"
            )

        # Step 2: Generate quiz questions
        result = quiz_service.generate_quiz(text_content)

        # Convert to list format
        questions_list = [question.model_dump() for question in result.questions]

        # Return JUST the questions array
        return questions_list

    except HTTPException:
        raise
    except UnicodeDecodeError as e:
        logger.error(f"File encoding error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read file (encoding issue): {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Quiz validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Read and generate quiz failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file and generate quiz: {str(e)}"
        )


@router.post("/read-and-push")
async def read_and_push_quiz(
    request: ReadAndPushQuizRequest,
    current_user=Depends(get_current_app),
    quiz_service: QuizGenerationService = Depends(get_quiz_service)
):
    """
    Read text from a local file, generate quiz questions, and push them to the configured external API.
    Uses the URL from QUIZ_EXTERNAL_API_URL environment variable or default config.

    Args:
        request: Contains the file path to read
        current_user: Authenticated user
        quiz_service: Quiz generation service

    Returns:
        Generated questions and response from external API
    """
    try:
        # Step 1: Read the file
        file_path = Path(request.file_path)

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_path}"
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=400,
                detail=f"Path is not a file: {request.file_path}"
            )

        # Read the file content
        logger.info(f"Reading file: {file_path}")
        text_content = file_path.read_text(encoding='utf-8')

        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail=f"File is empty: {request.file_path}"
            )

        # Step 2: Generate quiz questions
        result = quiz_service.generate_quiz(text_content)

        # Convert to list format
        questions_list = [question.model_dump() for question in result.questions]

        # Step 3: Send to configured external API
        async with httpx.AsyncClient(verify=False) as client:  # verify=False for localhost with self-signed cert
            headers = {"Content-Type": "application/json"}

            external_response = await client.post(
                SETTINGS.external_api_url,
                json=questions_list,  # Send questions array directly
                headers=headers,
                timeout=float(SETTINGS.external_api_timeout)
            )

            external_response.raise_for_status()

        return {
            "status": "success",
            "file_path": request.file_path,
            "text_length": len(text_content),
            "question_count": len(questions_list),
            "questions": questions_list,
            "external_api_url": SETTINGS.external_api_url,
            "external_api_response": {
                "status_code": external_response.status_code,
                "response": external_response.json() if external_response.text else None
            },
            "processed_by": current_user.get("sub", "unknown")
        }

    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"External API call failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to push questions to external API ({SETTINGS.external_api_url}): {str(e)}"
        )
    except UnicodeDecodeError as e:
        logger.error(f"File encoding error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read file (encoding issue): {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Quiz validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Read and push quiz failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file and generate quiz: {str(e)}"
        )


@router.post("/generate-and-send")
async def generate_and_send_quiz(
    request: SendQuizRequest,
    current_user=Depends(get_current_app),
    quiz_service: QuizGenerationService = Depends(get_quiz_service)
):
    """
    Generate quiz questions from provided text and send them to a custom external API URL.

    Args:
        request: Contains the source text, external API URL, and optional headers
        current_user: Authenticated user
        quiz_service: Quiz generation service

    Returns:
        Generated questions and response from external API
    """
    try:
        # Step 1: Generate quiz questions
        result = quiz_service.generate_quiz(request.text)

        # Convert to list format
        questions_list = [question.model_dump() for question in result.questions]

        # Step 2: Send to external API
        async with httpx.AsyncClient(verify=False) as client:  # verify=False for localhost with self-signed cert
            headers = {"Content-Type": "application/json"}

            # Add custom headers if provided (must be strings)
            if request.headers:
                for key, value in request.headers.items():
                    if isinstance(value, str):
                        headers[key] = value
                    else:
                        logger.warning(f"Skipping header {key}: value must be string, got {type(value)}")

            external_response = await client.post(
                request.external_api_url,
                json=questions_list,  # Send questions array directly
                headers=headers,
                timeout=30.0
            )

            external_response.raise_for_status()

        return {
            "status": "success",
            "question_count": len(questions_list),
            "questions": questions_list,
            "external_api_response": {
                "status_code": external_response.status_code,
                "response": external_response.json() if external_response.text else None
            },
            "processed_by": current_user.get("sub", "unknown")
        }

    except httpx.HTTPError as e:
        logger.error(f"External API call failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send questions to external API: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Quiz validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Quiz generation and send failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate and send quiz: {str(e)}"
        )
