# Step-Specific LLM Configuration Guide

## Overview

The translation service now supports using **different LLM providers and models for each step** of the translation pipeline:

1. **Grammar Correction** - Fix grammar and punctuation in source text
2. **Translation** - Translate corrected text to target language
3. **Quality Adjustment** - Review and improve translation quality

This allows you to optimize cost vs. quality for each step independently.

## Configuration Hierarchy

The system uses a **fallback hierarchy**:

```
Step-Specific Config → Global Config → Provider Default
```

- **Step-Specific:** `TRANSLATION_GRAMMAR_LLM_MODEL`, `TRANSLATION_TRANSLATION_LLM_MODEL`, etc.
- **Global:** `TRANSLATION_LLM_PROVIDER`, `TRANSLATION_LLM_MODEL`
- **Provider Default:** `gemini-1.5-pro` for Gemini, `gpt-4o` for OpenAI

## Configuration Options

### Global Configuration (Fallback)

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `TRANSLATION_LLM_PROVIDER` | `openai` or `gemini` | `gemini` | Default provider for all steps |
| `TRANSLATION_LLM_MODEL` | string | `None` | Default model (uses provider default if not set) |
| `TRANSLATION_LLM_TEMPERATURE` | float | `0.0` | Default temperature for all steps |
| `TRANSLATION_LLM_MAX_TOKENS` | integer | `None` | Max tokens for responses |

### Grammar Correction Step

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `TRANSLATION_GRAMMAR_LLM_PROVIDER` | `openai` or `gemini` | Falls back to global | Provider for grammar correction |
| `TRANSLATION_GRAMMAR_LLM_MODEL` | string | Falls back to global | Model for grammar correction |
| `TRANSLATION_GRAMMAR_LLM_TEMPERATURE` | float | Falls back to global | Temperature for grammar correction |

### Translation Step

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `TRANSLATION_TRANSLATION_LLM_PROVIDER` | `openai` or `gemini` | Falls back to global | Provider for translation |
| `TRANSLATION_TRANSLATION_LLM_MODEL` | string | Falls back to global | Model for translation |
| `TRANSLATION_TRANSLATION_LLM_TEMPERATURE` | float | Falls back to global | Temperature for translation |

### Quality Adjustment Step

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `TRANSLATION_ADJUSTMENT_LLM_PROVIDER` | `openai` or `gemini` | Falls back to global | Provider for quality adjustment |
| `TRANSLATION_ADJUSTMENT_LLM_MODEL` | string | Falls back to global | Model for quality adjustment |
| `TRANSLATION_ADJUSTMENT_LLM_TEMPERATURE` | float | Falls back to global | Temperature for quality adjustment |

## Configuration Examples

### Example 1: All Steps Use Same Model (Simple)

Just set global configuration:

```bash
# Use Gemini Flash for everything
TRANSLATION_LLM_PROVIDER=gemini
TRANSLATION_LLM_MODEL=gemini-1.5-flash
```

**Result:**
- Grammar: Gemini Flash
- Translation: Gemini Flash
- Adjustment: Gemini Flash

---

### Example 2: Fast Model for Grammar, Better Model for Translation

```bash
# Global defaults to Gemini Pro
TRANSLATION_LLM_PROVIDER=gemini
TRANSLATION_LLM_MODEL=gemini-1.5-pro

# Use Flash for grammar (faster, cheaper)
TRANSLATION_GRAMMAR_LLM_MODEL=gemini-1.5-flash
```

**Result:**
- Grammar: Gemini Flash ⚡ (faster, cheaper)
- Translation: Gemini Pro 🎯 (more accurate)
- Adjustment: Gemini Pro 🎯 (more accurate)

---

### Example 3: Different Provider for Quality Check

```bash
# Use Gemini for grammar and translation
TRANSLATION_LLM_PROVIDER=gemini
TRANSLATION_GRAMMAR_LLM_MODEL=gemini-2.5-flash
TRANSLATION_TRANSLATION_LLM_MODEL=gemini-2.5-flash

# Use OpenAI GPT-4o for quality adjustment (different perspective)
TRANSLATION_ADJUSTMENT_LLM_PROVIDER=openai
TRANSLATION_ADJUSTMENT_LLM_MODEL=gpt-4o
```

**Result:**
- Grammar: Gemini Flash ⚡
- Translation: Gemini Pro 🎯
- Adjustment: GPT-4o 👁️ (different AI for quality check)

---

### Example 4: Maximum Customization

```bash
# Global fallback
TRANSLATION_LLM_PROVIDER=gemini
TRANSLATION_LLM_TEMPERATURE=0.0

# Grammar: Fast and cheap
TRANSLATION_GRAMMAR_LLM_MODEL=gemini-1.5-flash
TRANSLATION_GRAMMAR_LLM_TEMPERATURE=0.1

# Translation: Accurate and deterministic
TRANSLATION_TRANSLATION_LLM_MODEL=gemini-1.5-pro
TRANSLATION_TRANSLATION_LLM_TEMPERATURE=0.0

# Adjustment: Creative quality improvements
TRANSLATION_ADJUSTMENT_LLM_PROVIDER=openai
TRANSLATION_ADJUSTMENT_LLM_MODEL=gpt-4o
TRANSLATION_ADJUSTMENT_LLM_TEMPERATURE=0.3
```

**Result:**
- Grammar: Gemini Flash with temp 0.1 ⚡
- Translation: Gemini Pro with temp 0.0 🎯
- Adjustment: GPT-4o with temp 0.3 🎨

## Setting Configuration

### In Azure App Service

1. Go to Azure Portal → Your App Service → **Configuration**
2. Click **+ New application setting**
3. Add each environment variable you want to customize
4. Click **Save** and restart the app

### In Local .env File

Create or edit `.env` in your project root:

```bash
# .env file
TRANSLATION_LLM_PROVIDER=gemini
TRANSLATION_GRAMMAR_LLM_MODEL=gemini-1.5-flash
TRANSLATION_TRANSLATION_LLM_MODEL=gemini-1.5-pro
TRANSLATION_ADJUSTMENT_LLM_PROVIDER=openai
TRANSLATION_ADJUSTMENT_LLM_MODEL=gpt-4o
```

### In Code (config.py defaults)

Edit `src/translation/config.py`:

```python
class TranslationSettings(BaseSettings):
    # Global defaults
    llm_provider: Literal["openai", "gemini"] = "gemini"
    llm_model: Optional[str] = None

    # Step-specific defaults (can override here instead of env vars)
    grammar_llm_model: Optional[str] = "gemini-1.5-flash"
    translation_llm_model: Optional[str] = "gemini-1.5-pro"
    adjustment_llm_provider: Optional[Literal["openai", "gemini"]] = "openai"
```

## Cost Optimization Strategies

### Strategy 1: "Fast Grammar, Accurate Translation"
```bash
TRANSLATION_GRAMMAR_LLM_MODEL=gemini-1.5-flash        # Cheap for simple task
TRANSLATION_TRANSLATION_LLM_MODEL=gemini-1.5-pro      # More expensive for main task
TRANSLATION_ADJUSTMENT_LLM_MODEL=gemini-1.5-flash     # Cheap for quick review
```

### Strategy 2: "All Flash for Speed"
```bash
TRANSLATION_LLM_MODEL=gemini-1.5-flash  # Fast and cheap for all steps
```

### Strategy 3: "Premium Quality"
```bash
TRANSLATION_LLM_PROVIDER=openai
TRANSLATION_LLM_MODEL=gpt-4o  # Best quality for all steps
```

### Strategy 4: "Hybrid Approach"
```bash
TRANSLATION_LLM_PROVIDER=gemini
TRANSLATION_GRAMMAR_LLM_MODEL=gemini-1.5-flash        # Fast
TRANSLATION_TRANSLATION_LLM_MODEL=gemini-1.5-pro      # Accurate
TRANSLATION_ADJUSTMENT_LLM_PROVIDER=openai            # Different perspective
TRANSLATION_ADJUSTMENT_LLM_MODEL=gpt-4o
```

## Model Comparison

### Gemini Models

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gemini-1.5-flash` | ⚡⚡⚡ Fast | 💰 Cheap | Grammar correction, quick tasks |
| `gemini-1.5-pro` | ⚡⚡ Medium | 💰💰 Moderate | Translation, main tasks |

### OpenAI Models

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gpt-4o` | ⚡⚡ Medium | 💰💰💰 Expensive | Quality adjustment, best accuracy |
| `gpt-4o-mini` | ⚡⚡⚡ Fast | 💰 Cheap | Grammar, quick tasks |

## Verification

To check which models are being used:

```bash
# Set your configuration
export TRANSLATION_GRAMMAR_LLM_MODEL=gemini-1.5-flash
export TRANSLATION_TRANSLATION_LLM_MODEL=gemini-1.5-pro

# Run verification script
python -c "
from src.translation.config import SETTINGS
print(f'Grammar: {SETTINGS.grammar_llm_model or SETTINGS.llm_model or \"(default)\"}')
print(f'Translation: {SETTINGS.translation_llm_model or SETTINGS.llm_model or \"(default)\"}')
print(f'Adjustment: {SETTINGS.adjustment_llm_model or SETTINGS.llm_model or \"(default)\"}')
"
```

## Troubleshooting

### Issue: All steps use the same model even though I set step-specific config

**Cause:** Environment variables not loaded or typo in variable name

**Solution:**
1. Verify variable names are exact (case-sensitive)
2. Restart your application after setting env vars
3. Check variables are loaded: `echo $TRANSLATION_GRAMMAR_LLM_MODEL`

### Issue: "Invalid API key" error

**Cause:** Missing API key in Azure Key Vault for the provider

**Solution:**
- For OpenAI: Add `openai-key` secret to Key Vault
- For Gemini: Add `GeminiAPIKey` secret to Key Vault

### Issue: Configuration not taking effect in Azure

**Cause:** App not restarted after configuration change

**Solution:** Go to Azure Portal → Your App Service → Click **Restart**

## Technical Details

### Code Flow

1. `TranslationService.__init__()` creates three providers:
   ```python
   self.grammar_provider = create_llm_provider(azure_config, step="grammar")
   self.translation_provider = create_llm_provider(azure_config, step="translation")
   self.adjustment_provider = create_llm_provider(azure_config, step="adjustment")
   ```

2. Each method uses its specific provider:
   ```python
   def _correct_grammar(self, text: str) -> str:
       return self.grammar_provider.invoke(...)

   def _translate_text(self, text: str, ...) -> str:
       return self.translation_provider.invoke(...)

   def _adjust_translation(self, source_text: str, translated_text: str) -> str:
       return self.adjustment_provider.invoke(...)
   ```

### Files Modified

- ✅ `src/translation/config.py` - Added step-specific configuration fields
- ✅ `src/translation/clients.py` - Updated factory to support step parameter
- ✅ `src/translation/translator.py` - Creates three separate providers

## Backward Compatibility

✅ **Fully backward compatible!**

If you don't set any step-specific configuration, the system uses the global configuration exactly as before. Existing deployments will continue to work without any changes.

## Questions?

For support or questions about step-specific LLM configuration, contact the development team or open an issue in the repository.
