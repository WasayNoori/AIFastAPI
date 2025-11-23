"""
Test script for the Translation Workflow endpoints.
Demonstrates the complete workflow: Load -> Grammar Correction -> Translation -> Save
"""

import requests
import json
from pathlib import Path

# Configuration
API_URL_BASE = "http://localhost:8000/translation/workflow"
YOUR_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0Iiwicm9sZSI6ImFkbWluIiwiYXBwX2lkIjoidGVzdF9hcHAiLCJleHAiOjE3NjI3NjAzOTJ9.S9pZdNc2PHZT_JOMAZT_-_jVzYrGa5wfNPL6jSJzesM"

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_complete_workflow(text: str, source_lang: str = "en", target_lang: str = "FR", correct_grammar: bool = True):
    """
    Test the complete workflow in one API call

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        correct_grammar: Whether to apply grammar correction
    """
    print_section("COMPLETE WORKFLOW TEST")

    headers = {
        "Authorization": f"Bearer {YOUR_JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "source_language": source_lang,
        "target_language": target_lang,
        "correct_grammar": correct_grammar
    }

    try:
        response = requests.post(
            f"{API_URL_BASE}/complete",
            json=payload,
            headers=headers
        )

        print(f"Status Code: {response.status_code}\n")

        if response.status_code == 200:
            data = response.json()
            result = data.get("workflow_result", {})

            # Step 1: Original
            print("STEP 1 - Original Text:")
            print("-" * 70)
            original = result.get("original", {})
            print(f"Character Count: {original.get('char_count')}")
            print(f"Word Count: {original.get('word_count')}")
            print(f"Text: {original.get('text')[:200]}...")

            # Step 2: Corrected and Split
            print("\nSTEP 2 - Grammar Corrected & Split:")
            print("-" * 70)
            corrected = result.get("corrected_and_split", {})
            print(f"Grammar Correction Applied: {corrected.get('grammar_correction_applied')}")
            print(f"Sentence Count: {corrected.get('sentence_count')}")
            print(f"\nCorrected Text:")
            print(corrected.get('corrected_text')[:300])
            print(f"\nFirst 3 Sentences:")
            for sentence in corrected.get('sentences', [])[:3]:
                print(f"  {sentence}")

            # Step 3: Translated
            print("\nSTEP 3 - Translated:")
            print("-" * 70)
            translated = result.get("translated", {})
            print(f"Source Language: {translated.get('source_language')}")
            print(f"Target Language: {translated.get('target_language')}")
            print(f"\nTranslated Text:")
            print(translated.get('translated_text'))

            print(f"\nWorkflow Completed: {result.get('workflow_completed')}")

        else:
            print("Error Response:")
            print(json.dumps(response.json(), indent=2))

    except Exception as e:
        print(f"Error: {e}")


def test_individual_steps(text: str):
    """
    Test each workflow step individually

    Args:
        text: Text to process
    """
    print_section("TESTING INDIVIDUAL STEPS")

    headers = {
        "Authorization": f"Bearer {YOUR_JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Step 1: Load Text
    print("\nStep 1: Load Text")
    print("-" * 70)
    payload = {"text": text, "source_language": "en", "target_language": "FR"}
    response = requests.post(f"{API_URL_BASE}/step1/load", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json().get("result", {})
        print(f"✓ Loaded: {result.get('word_count')} words, {result.get('char_count')} characters")
    else:
        print(f"✗ Failed: {response.status_code}")

    # Step 2: Correct and Split
    print("\nStep 2: Correct Grammar and Split")
    print("-" * 70)
    payload = {"text": text, "source_language": "en", "correct_grammar": True}
    response = requests.post(f"{API_URL_BASE}/step2/correct-and-split", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json().get("result", {})
        print(f"✓ Split into {result.get('sentence_count')} sentences")
        print(f"  Grammar correction: {result.get('grammar_correction_applied')}")
        corrected_text = result.get('corrected_text')
    else:
        print(f"✗ Failed: {response.status_code}")
        return

    # Step 3: Translate
    print("\nStep 3: Translate with DeepL")
    print("-" * 70)
    payload = {"text": corrected_text, "target_language": "FR"}
    response = requests.post(f"{API_URL_BASE}/step3/translate", json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json().get("result", {})
        print(f"✓ Translated: {result.get('source_language')} -> {result.get('target_language')}")
        print(f"  Translation: {result.get('translated_text')[:200]}...")
    else:
        print(f"✗ Failed: {response.status_code}")


def test_file_operations():
    """Test loading and saving files"""
    print_section("FILE OPERATIONS TEST")

    headers = {
        "Authorization": f"Bearer {YOUR_JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Test saving a file
    print("\nTest: Save File")
    print("-" * 70)
    test_content = "This is a test file created by the workflow API."
    save_payload = {
        "text": test_content,
        "file_path": "test_output.txt"
    }

    response = requests.post(
        f"{API_URL_BASE}/save-file",
        json=save_payload,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ {result.get('message')}")
        print(f"  File: {result.get('file_path')}")
    else:
        print(f"✗ Failed to save: {response.status_code}")

    # Test loading a file
    print("\nTest: Load File")
    print("-" * 70)
    load_payload = {
        "file_path": "test_output.txt"
    }

    response = requests.post(
        f"{API_URL_BASE}/load-file",
        json=load_payload,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            print(f"✓ {result.get('message')}")
            print(f"  File Size: {result.get('file_size')} bytes")
            print(f"  Content: {result.get('text')}")
        else:
            print(f"✗ {result.get('message')}")
    else:
        print(f"✗ Failed to load: {response.status_code}")


def test_workflow_from_file(file_path: str, target_lang: str = "FR"):
    """
    Complete workflow test reading from a file

    Args:
        file_path: Path to input text file
        target_lang: Target language for translation
    """
    print_section(f"WORKFLOW FROM FILE: {file_path}")

    # Read the file
    try:
        text = Path(file_path).read_text(encoding="utf-8")
        print(f"✓ Loaded file: {len(text)} characters")

        # Run complete workflow
        test_complete_workflow(text, target_lang=target_lang)

    except Exception as e:
        print(f"✗ Failed to read file: {e}")


if __name__ == "__main__":
    # Sample text for testing
    sample_text = """
    This is sample text for testing workflow. It contain some grammar errors.
    The system will correct grammar, split into sentence, and translate to French.
    Let see how it work!
    """

    # Test 1: Complete workflow with sample text
    test_complete_workflow(sample_text.strip(), target_lang="FR", correct_grammar=True)

    # Test 2: Individual steps
    # test_individual_steps(sample_text.strip())

    # Test 3: File operations
    # test_file_operations()

    # Test 4: Workflow from file (uncomment and update path)
    # test_workflow_from_file(r"C:\Translations\Scripts\English Scripts\25SWEssParts02_02.txt", target_lang="FR")
