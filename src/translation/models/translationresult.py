from pydantic import BaseModel

class TranslationResult(BaseModel):
    translation: str
    glossary_entries: int
    word_count: int
    processed_by: str
    status: str
    message: str
    blob_path: str
    original_text: str
    translated_text: str