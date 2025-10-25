# LLM Provider Abstraction Guide

## Overview

The translation module now uses a flexible LLM provider abstraction that allows you to easily switch between different AI models (OpenAI, Anthropic/Claude, Google Gemini) without modifying service code.

## Architecture

```
┌─────────────────────────────────────┐
│  Translation Services               │
│  (translator.py, etc.)              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  LLM Provider Factory               │
│  (clients.py)                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  LLM Provider Abstraction           │
│  (llm_provider.py)                  │
│  ├─ OpenAIProvider                  │
│  ├─ AnthropicProvider               │
│  └─ GeminiProvider                  │
└─────────────────────────────────────┘
```

## Configuration

### Via Environment Variables

Set the provider type and model configuration using environment variables:

```bash
# Choose provider (openai, anthropic, or gemini)
export TRANSLATION_LLM_PROVIDER=anthropic

# Optional: Specify model (uses provider default if not set)
export TRANSLATION_LLM_MODEL=claude-3-5-sonnet-20241022

# Optional: Set temperature (default: 0.0)
export TRANSLATION_LLM_TEMPERATURE=0.7

# Optional: Set max tokens
export TRANSLATION_LLM_MAX_TOKENS=4096
```

### Via config.py

Edit `src/translation/config.py` to change defaults:

```python
class TranslationSettings(BaseSettings):
    llm_provider: Literal["openai", "anthropic", "gemini"] = "openai"
    llm_model: Optional[str] = None  # Uses provider's default
    llm_temperature: float = 0.0
    llm_max_tokens: Optional[int] = None
```

## Supported Providers

### 1. OpenAI (Default)

**Default Model:** `gpt-4o`

**Azure Key Vault Secret:** `openai-key`

**Example Configuration:**
```bash
export TRANSLATION_LLM_PROVIDER=openai
export TRANSLATION_LLM_MODEL=gpt-4o-mini  # Optional: use cheaper model
```

### 2. Anthropic (Claude)

**Default Model:** `claude-3-5-sonnet-20241022`

**Azure Key Vault Secret:** `anthropic-key`

**Example Configuration:**
```bash
export TRANSLATION_LLM_PROVIDER=anthropic
export TRANSLATION_LLM_MODEL=claude-3-5-sonnet-20241022
```

**Setup Required:**
1. Add Anthropic API key to Azure Key Vault with name: `anthropic-key`
2. Install dependency: `pip install langchain-anthropic`

### 3. Google Gemini

**Default Model:** `gemini-1.5-pro`

**Azure Key Vault Secret:** `GeminiAPIKey` (already configured)

**Example Configuration:**
```bash
export TRANSLATION_LLM_PROVIDER=gemini
export TRANSLATION_LLM_MODEL=gemini-1.5-flash  # Optional: use faster model
```

**Setup Required:**
1. Install dependency: `pip install langchain-google-genai`

## Switching Providers

### Method 1: Environment Variables (Recommended for Azure)

In Azure App Service, set the Application Setting:

1. Go to Azure Portal → Your App Service → Configuration
2. Add new application setting:
   - Name: `TRANSLATION_LLM_PROVIDER`
   - Value: `anthropic` (or `openai`, `gemini`)
3. Save and restart the app

### Method 2: Local Development

Create or update `.env` file:

```bash
# .env
TRANSLATION_LLM_PROVIDER=anthropic
TRANSLATION_LLM_MODEL=claude-3-5-sonnet-20241022
TRANSLATION_LLM_TEMPERATURE=0.0
```

### Method 3: Code Changes

Edit `src/translation/config.py`:

```python
llm_provider: Literal["openai", "anthropic", "gemini"] = "anthropic"  # Change here
```

## How It Works

### Before (Old Code)

```python
class TranslationService:
    def __init__(self, azure_config: AzureKeyVaultConfig):
        self.api_key = azure_config.get_secret("openai-key")
        self.chat_model = ChatOpenAI(api_key=self.api_key)  # Hardcoded to OpenAI
```

### After (New Code)

```python
class TranslationService:
    def __init__(self, azure_config: AzureKeyVaultConfig):
        self.llm_provider = create_llm_provider(azure_config)  # Flexible provider
```

The factory function `create_llm_provider()` reads the configuration and returns the appropriate provider instance.

## Provider Defaults

| Provider | Default Model | Temperature | Max Tokens |
|----------|--------------|-------------|------------|
| OpenAI | gpt-4o | 0.0 | Not set |
| Anthropic | claude-3-5-sonnet-20241022 | 0.0 | Not set |
| Gemini | gemini-1.5-pro | 0.0 | Not set |

## API Key Requirements

Ensure the following secrets are configured in Azure Key Vault (`https://aifastapi.vault.azure.net`):

| Provider | Secret Name | Status |
|----------|------------|--------|
| OpenAI | `openai-key` | ✅ Configured |
| Anthropic | `anthropic-key` | ⚠️ Needs to be added |
| Gemini | `GeminiAPIKey` | ✅ Configured |

## Testing Different Providers

### Test Locally

```python
# In Python shell or test script
from src.services.azure_config import AzureKeyVaultConfig
from src.translation.clients import create_llm_provider
import os

# Test OpenAI
os.environ['TRANSLATION_LLM_PROVIDER'] = 'openai'
provider = create_llm_provider(AzureKeyVaultConfig("https://aifastapi.vault.azure.net"))
print(f"Provider: {type(provider).__name__}, Model: {provider.model}")

# Test Anthropic
os.environ['TRANSLATION_LLM_PROVIDER'] = 'anthropic'
provider = create_llm_provider(AzureKeyVaultConfig("https://aifastapi.vault.azure.net"))
print(f"Provider: {type(provider).__name__}, Model: {provider.model}")
```

### Test via API

```bash
# Test translation endpoint with current provider
curl -X POST "https://your-app.azurewebsites.net/translation/TranslateChain" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "blob_path": "https://...",
    "input_language": "en",
    "output_language": "fr",
    "glossary": {"Dome": "Dôme"}
  }'
```

## Dependencies

Make sure to install required packages:

```bash
# For OpenAI (already installed)
pip install langchain-openai

# For Anthropic (new - needs to be added)
pip install langchain-anthropic

# For Gemini (new - needs to be added)
pip install langchain-google-genai
```

## Troubleshooting

### Error: "Unsupported LLM provider"

**Cause:** Invalid provider name in configuration

**Solution:** Ensure `TRANSLATION_LLM_PROVIDER` is one of: `openai`, `anthropic`, `gemini`

### Error: "Failed to get secret 'anthropic-key'"

**Cause:** Anthropic API key not in Azure Key Vault

**Solution:** Add the secret to Azure Key Vault with name `anthropic-key`

### Error: ModuleNotFoundError: langchain_anthropic

**Cause:** Missing dependency

**Solution:** Install with `pip install langchain-anthropic`

## Benefits of This Abstraction

1. **Easy Switching:** Change providers via environment variable
2. **Cost Optimization:** Switch to cheaper models for testing
3. **Provider Redundancy:** Fallback to alternative if one fails
4. **Future-Proof:** Easy to add new providers (Azure OpenAI, Mistral, etc.)
5. **Centralized Config:** All LLM settings in one place

## Adding a New Provider

To add support for a new LLM provider:

1. Create a new provider class in `llm_provider.py`:

```python
class NewProvider(LLMProvider):
    def get_default_model(self) -> str:
        return "model-name"

    def create_client(self) -> BaseChatModel:
        return NewProviderClient(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            **self.kwargs
        )
```

2. Update `clients.py` factory function:

```python
elif provider_type == "newprovider":
    api_key = azure_config.get_secret("newprovider-key")
    return NewProvider(api_key=api_key, model=SETTINGS.llm_model, ...)
```

3. Update `config.py` type hints:

```python
llm_provider: Literal["openai", "anthropic", "gemini", "newprovider"] = "openai"
```

## Files Modified

- ✅ `src/translation/llm_provider.py` - New abstraction layer
- ✅ `src/translation/clients.py` - Factory function
- ✅ `src/translation/config.py` - Configuration settings
- ✅ `src/translation/translator.py` - Refactored to use abstraction
- ✅ `src/translation/translationLangChain.py` - Refactored to use abstraction
- ✅ `src/translation/summarizeLangChain.py` - Refactored to use abstraction

## Questions?

For support or questions about the LLM provider abstraction, contact the development team.
