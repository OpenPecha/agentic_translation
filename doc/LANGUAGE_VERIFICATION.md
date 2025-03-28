# Language Verification Feature

## Overview

The Language Verification feature adds robust target language validation to the translation process. It ensures that generated translations are actually in the requested target language by performing explicit verification at two stages:

1. **Early language detection** during the evaluation phase
2. **Language-aware extraction** when processing LLM responses

## Components

### 1. Language Verification Models

Two new models have been added to the system:

```python
# In models.py
class LanguageCheck(BaseModel):
    is_target_language: bool = Field(
        description="Whether the translation is actually in the specified target language",
    )
    language_issues: str = Field(
        description="Description of any issues with the target language if not in target language",
        default="",
    )

class Feedback(BaseModel):
    is_target_language: bool = Field(
        description="Whether the translation is actually in the specified target language",
        default=True,
    )
    language_issues: str = Field(
        description="Description of any issues with the target language if not in target language",
        default="",
    )
    # Existing fields...
```

### 2. Language Verification Prompt

A dedicated prompt was added to perform fast language detection:

```python
# In prompts.py
def get_language_check_prompt(translation, language="English"):
    """Generate a prompt to verify if a translation is in the target language."""
    return f"""Verify if this text is actually written in {language}:

Translation to check:
{translation}

CRITICAL TASK:
1. First, determine if this text is primarily written in {language}
2. Check for any sections that might be in a different language
3. Verify that technical terms are appropriately handled in {language}

Your response must provide:
1. is_target_language: Whether the text is actually in {language} (true/false)
2. language_issues: If not in {language}, describe what language it appears to be in and any specific issues

IMPORTANT: This check is only about the language used, not about translation quality or correctness.
"""
```

### 3. Fast-Fail Verification in Evaluation

The evaluation process was updated to validate language as its first step:

```python
# In evaluation.py
def check_translation_language(translation: str, language: str = "English") -> LanguageCheck:
    """Check if the translation is in the target language."""
    language_check_prompt = get_language_check_prompt(translation, language=language)
    language_check = llm.with_structured_output(LanguageCheck).invoke(language_check_prompt)
    return language_check

def llm_call_evaluator(state: State):
    # First check if the translation is in the target language
    language_check = check_translation_language(state['translation'][-1], language=language)
    
    # If not in target language, return early with language issue feedback
    if not language_check.is_target_language:
        # ...provide language error feedback and skip remaining evaluation
        return {
            "is_target_language": False,
            "language_issues": language_check.language_issues,
            # ...other state updates
        }
    
    # Only proceed with full evaluation if language is correct
    # ...regular evaluation logic
```

### 4. Workflow Integration

The routing logic was updated to handle language issues specifically:

```python
# In evaluation.py
def route_structured(state: State):
    """Route based on language and formatting evaluation results."""
    # First check if the translation is in the target language
    if state.get("is_target_language") is False:
        return "Wrong Language"
    
    # Then check formatting
    # ...existing formatting checks
```

### 5. Language-Aware Extraction

The translation extraction system was enhanced to be language-aware:

```python
# In utils.py
def get_translation_extraction_prompt(source_text, llm_response, language="English"):
    """Generate a few-shot prompt for translation extraction with language-specific examples."""
    system_message = SystemMessage(content=f"""You are an expert assistant specializing in extracting translations in {language} from text. Your task is to:

    1. Identify the actual translation portion of the text that is in {language}
    2. Extract ONLY the {language} translation
    3. VERIFY that the extracted text is actually in {language}
    
    CRITICAL: If the text contains translation in a language other than {language}, do NOT extract it. Your extracted text MUST be entirely in {language}.
    """)
    
    # ...multilingual example handling
```

## Implementation Details

1. **Multilingual Examples**: The system contains few-shot examples in English, Chinese, Italian, and Russian to improve language detection and extraction capabilities.

2. **Fast-Fail Approach**: Language verification occurs at the beginning of evaluation, saving processing time by not evaluating translations in the wrong language.

3. **Maximum Iterations**: The system allows up to 3 maximum translation iterations (configurable in `config.py`). This iteration count includes any attempts with wrong language.

4. **Explicit Feedback**: When language issues are detected, detailed feedback about the language problem is captured in the state and included in feedback history.

## Usage Notes

1. The language verification system can handle all target languages supported by the underlying LLM, including English, Chinese, Hindi, Italian, Russian, etc.

2. Errors in language are treated as critical issues that block further evaluation until fixed.

3. The system provides specific guidance about language issues detected to help improve subsequent translation attempts.

4. Language verification occurs both during extraction (to ensure only target language text is extracted) and during evaluation (to verify the extracted translation is in the correct language).