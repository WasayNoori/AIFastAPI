"""Test the step2 endpoint with sample data"""
import sys
import traceback

try:
    from src.services.azure_config import AzureKeyVaultConfig
    from src.translation.workflow_translation_service import WorkflowTranslationService

    print("[OK] Imports successful")

    # Initialize services
    azure_config = AzureKeyVaultConfig("https://aifastapi.vault.azure.net")
    workflow_service = WorkflowTranslationService(azure_config)
    print("[OK] Services initialized")

    # Test with the user's payload
    test_payload = {
        "text": "I live in Vancouver. Vancouver are beautiful.",
        "source_language": "en",
        "target_language": "EN",
        "correct_grammar": True
    }

    print(f"\n[TEST] Testing with payload:")
    print(f"  text: {test_payload['text']}")
    print(f"  source_language: {test_payload['source_language']}")
    print(f"  correct_grammar: {test_payload['correct_grammar']}")

    # Call the step2 method
    result = workflow_service.step2_correct_and_split(
        text=test_payload["text"],
        language=test_payload["source_language"],
        correct_grammar=test_payload["correct_grammar"]
    )

    print(f"\n[SUCCESS] Step 2 completed successfully!")
    print(f"\nResults:")
    print(f"  Grammar correction applied: {result.grammar_correction_applied}")
    print(f"  Corrected text: {result.corrected_text}")
    print(f"  Sentence count: {result.sentence_count}")
    print(f"  Sentences:")
    for sentence in result.sentences:
        print(f"    {sentence}")

except Exception as e:
    print(f"\n[ERROR] Error occurred: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
