"""
Test script for the /analyzetext endpoint.
Reads script from a file or string and sends to the API.
"""

import requests
import json
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/translation/analyzetext"  # Change port if needed
YOUR_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0Iiwicm9sZSI6ImFkbWluIiwiYXBwX2lkIjoidGVzdF9hcHAiLCJleHAiOjE3NjM2NzA5MjR9.l8v3xcX8SreZKwDksiNuUqMfOb0DJk2QKtD-KtCdQOQ"  # Replace with your actual token

def test_analyzetext_from_file(file_path: str, language: str = "en", correct_grammar: bool = False):
    """
    Test the analyzetext endpoint by reading script from a file.

    Args:
        file_path: Path to text file containing the script
        language: Language code (en, fr, de)eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0Iiwicm9sZSI6ImFkbWluIiwiYXBwX2lkIjoidGVzdF9hcHAiLCJleHAiOjE3NjI3OTQ5OTh9.W9gfUzi84Jwo4xGzfzEYEx-qC5ufk-k4mOzsfLGx8tI
        correct_grammar: Whether to apply grammar correction
    """
    # Read the script from file
    script_text = Path(file_path).read_text(encoding="utf-8")

    # Prepare the request
    headers = {
        "Authorization": f"Bearer {YOUR_JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": script_text,
        "language": language,
        "correct_grammar": correct_grammar
    }

    # Send the request
    print(f"Sending request to {API_URL}...")
    print(f"Script length: {len(script_text)} characters")
    print(f"Correct grammar: {correct_grammar}")
    print("-" * 50)

    try:
        response = requests.post(API_URL, json=payload, headers=headers)

        # Print response
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nSentence Count: {data.get('sentenceCount', 0)}")
            print("\nSentences:")
            print("-" * 50)
            for sentence in data.get('sentences', []):
                print(sentence)  # Print directly without JSON escaping
        else:
            print("\nResponse:")
            print(json.dumps(response.json(), indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    except json.JSONDecodeError:
        print(f"Response text: {response.text}")


def test_analyzetext_from_string(script_text: str, language: str = "en", correct_grammar: bool = False):
    """
    Test the analyzetext endpoint with a string.

    Args:
        script_text: The script text to analyze
        language: Language code (en, fr, de)
        correct_grammar: Whether to apply grammar correction
    """
    # Prepare the request
    headers = {
        "Authorization": f"Bearer {YOUR_JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": script_text,
        "language": language,
        "correct_grammar": correct_grammar
    }

    # Send the request
    print(f"Sending request to {API_URL}...")
    print(f"Script length: {len(script_text)} characters")
    print(f"Correct grammar: {correct_grammar}")
    print("-" * 50)

    try:
        response = requests.post(API_URL, json=payload, headers=headers)

        # Print response
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nSentence Count: {data.get('sentenceCount', 0)}")
            print("\nSentences:")
            print("-" * 50)
            for sentence in data.get('sentences', []):
                print(sentence)  # Print directly without JSON escaping
        else:
            print("\nResponse:")
            print(json.dumps(response.json(), indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    except json.JSONDecodeError:
        print(f"Response text: {response.text}")


if __name__ == "__main__":
    # Example 1: Test with a sample string (comment out if not needed)
    # sample_script = """
    # Hello world! This is a test script.
    # It has multiple lines and "quotes" in it.
    # Let's see how it handles special characters: apostrophes, dashes — and more.
    # """
    #
    # print("=" * 50)
    # print("Example 1: Testing with sample string")
    # print("=" * 50)
    # test_analyzetext_from_string(sample_script, language="en", correct_grammar=False)

    # Example 2: Test with a file - UPDATE THE PATH BELOW
    print("=" * 50)
    print("Testing from file")
    print("=" * 50)
    test_analyzetext_from_file(r"C:\Translations\Scripts\English Scripts\25SWEssParts02_11.txt", language="en", correct_grammar=True)
