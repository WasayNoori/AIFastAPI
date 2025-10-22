import spacy
from typing import List

class Sentence:
    """Custom class to hold sentence text and its number/position."""
    
    def __init__(self, text: str, number: int):
        self.Text = text
        self.Number = number
    
    def __repr__(self):
        return f"Sentence(Number={self.Number}, Text='{self.Text[:50]}...')"

def split_text_file(file_path: str, language: str = "en") -> List[Sentence]:
    """
    Reads a text file and splits it into sentences using SpaCy.
    
    Args:
        file_path (str): Path to the text file to read
        language (str): Language code - 'en' (English), 'fr' (French), or 'de' (German)
    
    Returns:
        List[Sentence]: List of Sentence objects with Text and Number attributes
    
    Raises:
        ValueError: If unsupported language is provided
        FileNotFoundError: If the file doesn't exist
    """
    # Map language codes to SpaCy models
    language_models = {
        "en": "en_core_web_sm",
        "fr": "fr_core_news_sm",
        "de": "de_core_news_sm"
    }
    
    # Validate language
    if language not in language_models:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported languages: {', '.join(language_models.keys())}"
        )
    
    # Load the appropriate SpaCy model
    nlp = spacy.load(language_models[language])
    
    # Read the text file
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Use SpaCy to split text into sentences
    doc = nlp(text)
    
    # Create list of Sentence objects
    sentences = []
    for i, sent in enumerate(doc.sents, start=1):
        sentence_text = sent.text.strip()
        if sentence_text:  # Only add non-empty sentences
            sentences.append(Sentence(text=sentence_text, number=i))
    
    return sentences


# Example usage
if __name__ == "__main__":
    # Test the function
    sentences = split_text_file("script.txt", language="en")
    
    print(f"Total Sentence={len(sentences)}")