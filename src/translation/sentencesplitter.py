import spacy
from typing import List
import re

class Sentence:
    """Custom class to hold sentence text and its number/position."""
    
    def __init__(self, text: str, number: int):
        self.Text = text
        self.Number = number
    
    def __repr__(self):
        return f"Sentence(Number={self.Number}, Text='{self.Text[:50]}...')"


def is_valid_sentence_start(text: str) -> bool:
    """
    Check if a sentence has a valid start.
    Invalid starts include:
    - Starting with a comma
    - Starting with a lowercase letter after a comma

    Args:
        text (str): The sentence text to validate

    Returns:
        bool: True if the sentence start is valid, False otherwise
    """
    if not text:
        return False

    # Check if starts with comma (with optional whitespace)
    if re.match(r'^\s*,', text):
        return False

    return True


def is_invalid_fragment(text: str) -> bool:
    """
    Check if a sentence is an invalid fragment that should be merged.
    Invalid fragments include:
    - Single word ending with a comma
    - Starting with a comma
    - Starting with a lowercase letter (not a valid sentence start)

    Args:
        text (str): The sentence text to validate

    Returns:
        bool: True if this is an invalid fragment, False otherwise
    """
    if not text:
        return False

    text_stripped = text.strip()

    # Check if starts with comma
    if text_stripped.startswith(','):
        return True

    # Check if it's a single word ending with comma
    # Single word = no spaces (except leading/trailing) and ends with comma
    if re.match(r'^\s*\S+,\s*$', text_stripped):
        return True

    # Check if starts with lowercase letter (invalid sentence start)
    # Get the first character that's actually a letter
    first_char_match = re.search(r'[a-zA-ZÀ-ÿ]', text_stripped)
    if first_char_match:
        first_letter = first_char_match.group(0)
        # If the first letter is lowercase, it's likely an invalid fragment
        if first_letter.islower():
            return True

    return False


def merge_invalid_fragments(sentences: List[str]) -> List[str]:
    """
    Merge invalid sentence fragments with the previous valid sentence.

    Args:
        sentences (List[str]): List of sentence strings from spaCy

    Returns:
        List[str]: List of merged sentences with invalid fragments combined
    """
    if not sentences:
        return []

    merged = []
    current = sentences[0]

    for i in range(1, len(sentences)):
        sentence = sentences[i]

        # If this sentence is an invalid fragment, merge with current
        if is_invalid_fragment(sentence):
            current = current + " " + sentence
        else:
            # Save the current accumulated sentence and start a new one
            merged.append(current)
            current = sentence

    # Don't forget the last sentence
    merged.append(current)

    return merged


def split_text(text: str, language: str = "en") -> List[Sentence]:
    """
    Splits text into sentences using SpaCy.
    
    Args:
        text (str): The text to split into sentences
        language (str): Language code - 'en' (English), 'fr' (French), or 'de' (German)
    
    Returns:
        List[Sentence]: List of Sentence objects with Text and Number attributes
    
    Raises:
        ValueError: If unsupported language is provided
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

    # Use SpaCy to split text into sentences
    doc = nlp(text)

    # Extract raw sentences from spaCy
    raw_sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    # Merge invalid fragments (sentences starting with comma, single words ending with comma, etc.)
    merged_sentences = merge_invalid_fragments(raw_sentences)

    # Create list of Sentence objects with renumbered positions
    sentences = []
    for i, sentence_text in enumerate(merged_sentences, start=1):
        if sentence_text:  # Only add non-empty sentences
            sentences.append(Sentence(text=sentence_text, number=i))

    return sentences


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
    # Read the text file
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Use the split_text function to split into sentences
    return split_text(text, language)


# Command line usage
if __name__ == "__main__":
    import sys
    import json
    
    # Ensure proper output handling for .NET process communication
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    if len(sys.argv) < 2:
        error_msg = json.dumps({"error": "Usage: python sentencesplitter.py <file_path> [language]"})
        print(error_msg, flush=True)
        sys.exit(1)
    
    file_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "en"
    
    try:
        sentences = split_text_file(file_path, language=language)
        
        # Output as JSON for easy parsing by the .NET application
        result = {
            "total_sentences": len(sentences),
            "sentences": [{"number": s.Number, "text": s.Text} for s in sentences]
        }
        
        # Flush output immediately to prevent pipe issues
        output = json.dumps(result, ensure_ascii=True, indent=2)
        print(output, flush=True)
        
    except FileNotFoundError:
        error_output = json.dumps({"error": f"File not found: {file_path}"})
        print(error_output, flush=True)
        sys.exit(1)
    except Exception as e:
        error_output = json.dumps({"error": str(e)})
        print(error_output, flush=True)
        sys.exit(1)
