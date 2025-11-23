"""
Bulk Translation Script
Processes multiple text files through the complete translation workflow.
"""

import os
import csv
import requests
from pathlib import Path
from typing import List

# =============================================================================
# CONFIGURATION - Modify these values as needed
# =============================================================================

# Source folder where subfolders and CSV will be created
SOURCE_FOLDER = r"C:\Translations\SandBox"

# List of text file paths to process
FILE_PATHS = [
    r"C:\Translations\Scripts\English Scripts\25SWEssParts02_02.txt",
    r"C:\Translations\Scripts\English Scripts\25SWEssParts02_03.txt"
  ]

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000/"  # Change if running on different host/port
API_ENDPOINT = "/translation/workflow/complete"

# Authentication token (get this from your auth flow)
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0Iiwicm9sZSI6ImFkbWluIiwiYXBwX2lkIjoidGVzdF9hcHAiLCJleHAiOjE3NjM4ODAwNzZ9.ZcClctWFhSPtcQtagfBfuXw9FO86SgujpQD4DLY_P1M"  # Set your Bearer token here

# Target language for translation
TARGET_LANGUAGE = "FR"

# =============================================================================
# SCRIPT LOGIC - Do not modify below unless necessary
# =============================================================================


def get_auth_headers() -> dict:
    """Get authorization headers for API calls."""
    if not AUTH_TOKEN:
        raise ValueError("AUTH_TOKEN is not set. Please set your Bearer token.")
    return {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }


def call_workflow_api(text: str, target_language: str = "FR") -> dict:
    """
    Call the /workflow/complete API endpoint.

    Args:
        text: The text to process
        target_language: Target language code (default: FR)

    Returns:
        API response as dictionary
    """
    url = f"{API_BASE_URL}{API_ENDPOINT}"
    payload = {
        "text": text,
        "source_language": "en",
        "target_language": target_language,
        "correct_grammar": True
    }

    response = requests.post(
        url,
        headers=get_auth_headers(),
        json=payload,
        timeout=120  # Longer timeout for large texts
    )
    response.raise_for_status()
    return response.json()


def process_file(file_path: str, source_folder: str, target_language: str = "FR") -> dict:
    """
    Process a single text file through the workflow.

    Args:
        file_path: Path to the text file
        source_folder: Base folder for output
        target_language: Target language for translation

    Returns:
        Dictionary with processing results
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"  ERROR: File not found: {file_path}")
        return {"error": f"File not found: {file_path}"}

    # Read the input text file
    text = file_path.read_text(encoding="utf-8")
    print(f"  Read {len(text)} characters from file")

    # Call the workflow API
    print(f"  Calling workflow API...")
    result = call_workflow_api(text, target_language)

    if result.get("status") != "success":
        print(f"  ERROR: API returned non-success status")
        return {"error": "API returned non-success status", "response": result}

    workflow_result = result.get("workflow_result", {})

    # Extract data from response
    corrected_data = workflow_result.get("corrected_and_split", {})
    translated_data = workflow_result.get("translated", {})

    english_sentences = corrected_data.get("sentences", [])
    english_sentence_count = corrected_data.get("sentence_count", 0)

    french_text = translated_data.get("translated_text", "")
    french_sentence_count = translated_data.get("translated_sentence_count", 0)

    # Create subfolder with the name of the text file (without extension)
    subfolder_name = file_path.stem
    subfolder_path = Path(source_folder) / subfolder_name
    subfolder_path.mkdir(parents=True, exist_ok=True)
    print(f"  Created subfolder: {subfolder_path}")

    # Save English Sentences.txt
    english_file = subfolder_path / "English Sentences.txt"
    english_content = "\n".join(english_sentences)
    english_file.write_text(english_content, encoding="utf-8")
    print(f"  Saved: {english_file}")

    # Save French Sentences.txt
    french_file = subfolder_path / "French Sentences.txt"
    french_file.write_text(french_text, encoding="utf-8")
    print(f"  Saved: {french_file}")

    return {
        "filename": file_path.name,
        "english_sentence_count": english_sentence_count,
        "french_sentence_count": french_sentence_count,
        "subfolder": str(subfolder_path)
    }


def update_csv(source_folder: str, results: List[dict]):
    """
    Update (append to) the CSV file with results.

    Args:
        source_folder: Folder where CSV should be saved
        results: List of result dictionaries
    """
    csv_path = Path(source_folder) / "translation_results.csv"

    # Check if file exists to determine if we need headers
    file_exists = csv_path.exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["filename", "english_sentence_count", "french_sentence_count"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Write header only if file doesn't exist
        if not file_exists:
            writer.writeheader()

        for result in results:
            if "error" not in result:
                writer.writerow({
                    "filename": result["filename"],
                    "english_sentence_count": result["english_sentence_count"],
                    "french_sentence_count": result["french_sentence_count"]
                })

    print(f"\nCSV updated: {csv_path}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Bulk Translation Script")
    print("=" * 60)

    # Validate configuration
    if not FILE_PATHS:
        print("ERROR: No file paths configured. Add paths to FILE_PATHS list.")
        return

    if not AUTH_TOKEN:
        print("ERROR: AUTH_TOKEN is not set. Please configure your Bearer token.")
        return

    # Ensure source folder exists
    source_folder = Path(SOURCE_FOLDER)
    source_folder.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {source_folder}")
    print(f"Files to process: {len(FILE_PATHS)}")
    print("-" * 60)

    results = []

    for i, file_path in enumerate(FILE_PATHS, 1):
        print(f"\n[{i}/{len(FILE_PATHS)}] Processing: {file_path}")
        try:
            result = process_file(file_path, str(source_folder), TARGET_LANGUAGE)
            results.append(result)

            if "error" not in result:
                print(f"  English sentences: {result['english_sentence_count']}")
                print(f"  French sentences: {result['french_sentence_count']}")
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({"error": str(e), "filename": Path(file_path).name})

    # Update CSV with results
    update_csv(str(source_folder), results)

    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Processed: {len([r for r in results if 'error' not in r])}/{len(FILE_PATHS)} files")
    print("=" * 60)


if __name__ == "__main__":
    main()
