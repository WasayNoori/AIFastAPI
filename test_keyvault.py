import os
import sys
import time
from dotenv import load_dotenv
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

load_dotenv()

print("Testing Azure Key Vault connectivity...")
print(f"Key Vault URL: {os.getenv('AZURE_KEY_VAULT_URL', 'Not set')}")

try:
    print("1. Creating DefaultAzureCredential...")
    start_time = time.time()
    credential = DefaultAzureCredential()
    print(f"   [OK] DefaultAzureCredential created in {time.time() - start_time:.2f}s")
    
    print("2. Creating SecretClient...")
    start_time = time.time()
    client = SecretClient(vault_url=os.getenv("AZURE_KEY_VAULT_URL"), credential=credential)
    print(f"   [OK] SecretClient created in {time.time() - start_time:.2f}s")
    
    print("3. Testing secret retrieval...")
    start_time = time.time()
    secret = client.get_secret("jwt-secret-key")
    print(f"   [OK] Secret retrieved in {time.time() - start_time:.2f}s")
    print(f"   Secret name: {secret.name}")
    print(f"   Secret value length: {len(secret.value)} characters")
    
    print("\n[SUCCESS] Key Vault connectivity test PASSED!")
    
except Exception as e:
    print(f"\n[FAILED] Key Vault connectivity test FAILED!")
    print(f"Error: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    sys.exit(1)