"""Test script to debug workflow service initialization"""
import sys
import traceback

try:
    from src.services.azure_config import AzureKeyVaultConfig
    print("[OK] AzureKeyVaultConfig imported successfully")

    azure_config = AzureKeyVaultConfig("https://aifastapi.vault.azure.net")
    print("[OK] AzureKeyVaultConfig initialized successfully")

    from src.translation.workflow_translation_service import WorkflowTranslationService
    print("[OK] WorkflowTranslationService imported successfully")

    workflow_service = WorkflowTranslationService(azure_config)
    print("[OK] WorkflowTranslationService initialized successfully")

    print("\n[SUCCESS] All initialization steps completed successfully!")

except Exception as e:
    print(f"\n[ERROR] Error occurred: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
