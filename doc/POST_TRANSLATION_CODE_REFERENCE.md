# Post-Translation System: Technical Reference

This document provides a detailed technical reference for the post-translation system codebase, focusing on implementation details, function signatures, and specific code patterns.

## Table of Contents

1. [Code Organization](#code-organization)
2. [Key Files](#key-files)
3. [Core Data Structures](#core-data-structures)
4. [Function Reference](#function-reference)
5. [Code Patterns](#code-patterns)
6. [Dependencies](#dependencies)
7. [Testing](#testing)
8. [Error Handling Implementation](#error-handling-implementation)

## Code Organization

The post-translation system is organized as follows:

```
tibetan_translator/
├── processors/
│   ├── __init__.py
│   ├── post_translation.py     # Main implementation
│   └── ...
├── models.py                   # Data models
├── utils.py                    # Shared utilities
├── config.py                   # Configuration
└── ...
examples/
├── post_translation_example.py # CLI interface
└── ...
tests/
├── test_post_translation.py    # Unit tests
└── ...
doc/
├── POST_TRANSLATION.md         # Conceptual overview
└── POST_TRANSLATION_CODE_REFERENCE.md  # This file
```

## Key Files

### `/tibetan_translator/processors/post_translation.py`

This is the main implementation file containing all core functions for the post-translation pipeline:

- `setup_logging()`: Configures dual console/file logging
- `analyze_term_frequencies()`: Analyzes term frequency across documents
- `generate_standardization_examples()`: Creates examples for terminology standardization
- `standardize_terminology()`: Selects optimal translations for terms
- `apply_standardized_terms()`: Updates documents with standardized terms
- `generate_word_by_word()`: Creates word-by-word mappings
- `post_process_corpus()`: Main pipeline function that orchestrates the process

### `/examples/post_translation_example.py`

The command-line interface for the post-translation system:

- Handles argument parsing
- Provides language detection from filenames
- Includes a sample workflow for demonstration
- Manages input/output file paths

### `/tests/test_post_translation.py`

Unit tests for post-translation functionality:

- Tests individual components with mock data
- Verifies correct handling of edge cases
- Includes integration tests for the full pipeline

## Core Data Structures

### Pydantic Models

The system uses Pydantic models for structured data validation:

```python
# WordStandardization model for standardized terms
class WordStandardization(BaseModel):
    standard_translation: str = Field(description="The standard translation of the word")
    tibetan_term: str = Field(description="The tibetan term to be standardized")
    rationale: str = Field(description="The rationale for the standardization")
    target_audience: str = Field(description="Ranked target audience for the standardization")

# PostTranslation model for standardized translations
class PostTranslation(BaseModel):
    standardised_translation: str = Field(description="The standardised translation")

# WordByWordTranslation model for word-by-word mapping
class WordByWordTranslation(BaseModel):
    word_by_word_translation: str = Field(description="The word by word translation")
```

### Term Frequency DataFrame

The frequency analysis produces a pandas DataFrame with the following structure:

| tibetan_term | translation_freq | translation_count |
|--------------|------------------|-------------------|
| བྱང་ཆུབ་སེམས     | bodhicitta (5); awakening mind (3); mind of enlightenment (1) | 3 |
| ཤེས་རབ་         | wisdom (8); prajna (2) | 2 |

### Standardized Terms Format

Standardized terms are stored as a list of dictionaries:

```python
[
    {
        "tibetan_term": "བྱང་ཆུབ་སེམས",
        "standard_translation": "awakening mind",
        "rationale": "This term appears in multiple contexts...",
        "target_audience": "practitioners, academics, general readers"
    },
    # More terms...
]
```

## Function Reference

### `analyze_term_frequencies(glossaries: List[Dict[str, Any]]) -> pd.DataFrame`

**Purpose**: Analyzes term frequencies across all glossaries to identify terms with multiple translations.

**Parameters**:
- `glossaries`: List of glossary entries from all documents

**Returns**: DataFrame with tibetan_term, translation_freq, and translation_count columns

**Implementation notes**:
- Uses nested dictionaries to track term → translation → count
- Sorts translations by frequency
- Formats frequencies as semicolon-separated string with counts

**Example usage**:
```python
term_freq = analyze_term_frequencies(all_glossaries)
```

### `generate_standardization_examples(glossary: pd.DataFrame, corpus: List[Dict[str, Any]], max_samples_per_term: int = 20, language: str = 'English') -> List[str]`

**Purpose**: Generates standardization examples for terms with multiple translations.

**Parameters**:
- `glossary`: DataFrame with tibetan_term and translation_freq columns
- `corpus`: List of document dictionaries with source, translation, and sanskrit
- `max_samples_per_term`: Maximum number of examples to include per term
- `language`: Target language for standardized terms

**Returns**: List of standardization example strings

**Implementation notes**:
- Filters for terms with multiple translations (translation_count > 1)
- Searches corpus for documents containing each term
- Limits examples to max_samples_per_term
- Includes language-specific standardization protocol

**Example usage**:
```python
examples = generate_standardization_examples(term_freq, corpus, language="Chinese")
```

### `standardize_terminology(examples: List[str], language: str = 'English') -> List[Dict[str, str]]`

**Purpose**: Standardizes terminology by selecting the best translation for each term.

**Parameters**:
- `examples`: List of standardization example strings
- `language`: Target language for standardized terms

**Returns**: List of dictionaries with standardized term data

**Implementation notes**:
- Uses LLM with structured output (WordStandardization model)
- Processes in batches of 30 for performance
- Implements multi-level retry logic
- Validates language compatibility
- Logs standardized terms for debugging

**Example usage**:
```python
standardized_terms = standardize_terminology(examples, language="Chinese")
```

### `apply_standardized_terms(corpus: List[Dict[str, Any]], standardized_glossary: pd.DataFrame) -> List[Dict[str, Any]]`

**Purpose**: Applies standardized terminology to all translations in the corpus.

**Parameters**:
- `corpus`: List of document dictionaries
- `standardized_glossary`: DataFrame with standardized terms

**Returns**: Updated corpus with standardized translations

**Implementation notes**:
- Only processes documents containing standardizable terms
- Creates document-specific glossaries
- Handles translation formats (string, list, JSON string)
- Uses the last/final translation in lists
- Preserves original translation as plaintext_translation
- Processes with batched LLM calls and retry logic

**Example usage**:
```python
updated_corpus = apply_standardized_terms(corpus, standardized_df)
```

### `generate_word_by_word(corpus: List[Dict[str, Any]], language: str = 'English') -> List[Dict[str, Any]]`

**Purpose**: Generates word-by-word translations for all documents in the corpus.

**Parameters**:
- `corpus`: List of document dictionaries with source and translation
- `language`: Target language for translations

**Returns**: Updated corpus with word-by-word translations

**Implementation notes**:
- Handles translation formats (string, list, JSON string)
- Uses language-specific examples in prompts
- Processes in batches of 20
- Implements multi-level retry logic
- Adds results to corpus as 'word_by_word_translation' field

**Example usage**:
```python
final_corpus = generate_word_by_word(updated_corpus, language="Chinese")
```

### `post_process_corpus(corpus: List[Dict[str, Any]], output_file: str = 'inputs_final_cleaned.json', glossary_file: str = 'standard_translation.csv', language: str = None) -> List[Dict[str, Any]]`

**Purpose**: Main function to run the full post-processing pipeline on a corpus.

**Parameters**:
- `corpus`: List of document dictionaries
- `output_file`: Path to save the final processed corpus
- `glossary_file`: Path to save the standardized glossary CSV
- `language`: Target language for translations (auto-detected if None)

**Returns**: Processed corpus with standardized translations and word-by-word mappings

**Implementation notes**:
- Auto-detects language from corpus if not specified
- Orchestrates the full pipeline
- Saves standardized glossary as CSV
- Outputs corpus as JSON or JSONL based on file extension
- Ensures required fields in output
- Handles various translation formats

**Example usage**:
```python
processed_corpus = post_process_corpus(corpus, "output.jsonl", "glossary.csv", "Chinese")
```

## Code Patterns

### Batch Processing Pattern

The system uses a common pattern for batch processing with retries:

```python
# Process in batches
batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

for batch_idx, batch in enumerate(tqdm(batches, desc="Processing")):
    try:
        # Try batch processing
        results = processor.batch(batch)
        # Process results...
    except Exception as e:
        logger.error(f"Error in batch {batch_idx+1}: {str(e)}")
        
        try:
            # Retry once
            results = processor.batch(batch)
            # Process results...
        except Exception as retry_e:
            logger.error(f"Error on retry: {str(retry_e)}")
            
            # Fall back to individual processing
            for item_idx, item in enumerate(batch):
                try:
                    result = processor.invoke(item)
                    # Process result...
                except Exception as item_e:
                    logger.error(f"Failed to process item: {str(item_e)}")
```

### Format Handling Pattern

Translation fields are handled consistently with this pattern:

```python
# Get translation value (could be string, list, or JSON string)
translation = doc.get('translation', '')

# Handle list case
if isinstance(translation, list) and translation:
    translation = translation[-1]  # Use last/final translation
    
# Handle JSON string case
elif isinstance(translation, str) and (
    (translation.startswith('[') and translation.endswith(']')) or
    (translation.startswith('{') and translation.endswith('}'))
):
    try:
        # Try to parse JSON
        parsed = json.loads(translation)
        
        # Extract based on type
        if isinstance(parsed, list) and parsed:
            translation = parsed[-1]  # Last item from list
        elif isinstance(parsed, dict) and 'translation' in parsed:
            translation = parsed['translation']  # Use translation field
        else:
            translation = str(parsed)  # Fallback to string representation
    except json.JSONDecodeError:
        # Not valid JSON, use as is
        pass
```

### Language Detection Pattern

The system uses a cascading pattern for language detection:

```python
# Try to detect language
language = None

# 1. Try command-line argument
if args.language:
    language = args.language
    
# 2. Try filename detection
elif "chinese" in input_filename.lower():
    language = "Chinese"
# etc. for other languages...

# 3. Try field in documents
else:
    for doc in corpus:
        if 'language' in doc and doc['language']:
            language = doc['language']
            break
            
# 4. Fallback to default
if language is None:
    language = "English"
```

## Dependencies

### Core Dependencies

- **pandas**: Used for DataFrame operations and CSV handling
- **tqdm**: Progress bar for long-running operations
- **pydantic**: Data validation and structured output
- **langchain**: LLM interaction and structured outputs

### LLM Integration

The system uses Anthropic Claude through Langchain:

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

# Initialize model
llm = ChatAnthropic(model=LLM_MODEL_NAME, max_tokens=MAX_TOKENS)

# Create structured output provider
word_standardizer = llm.with_structured_output(WordStandardization)
```

### Logging Configuration

The system uses Python's built-in logging with a dual-handler setup:

```python
# Console handler for user-friendly output
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(message)s'))

# File handler for detailed debugging
file_handler = logging.FileHandler("post_translation_debug.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
```

## Testing

### Unit Testing

The system includes comprehensive unit tests focusing on:

1. `test_analyze_term_frequencies`: Tests term frequency analysis
2. `test_generate_standardization_examples`: Tests example generation
3. `test_standardize_terminology`: Tests terminology standardization with mocked LLM
4. `test_apply_standardized_terms`: Tests applying terms with mocked LLM
5. `test_generate_word_by_word`: Tests word-by-word generation with mocked LLM
6. `test_post_process_corpus`: Tests the full pipeline with mocked components

### Mock Usage Pattern

Tests use mocks to avoid LLM API calls:

```python
@patch('tibetan_translator.processors.post_translation.llm')
def test_standardize_terminology(self, mock_llm):
    # Set up mock
    mock_structured_output = MagicMock()
    mock_structured_output.batch.return_value = [
        MagicMock(
            standard_translation="awakening mind",
            tibetan_term="བྱང་ཆུབ་སེམས",
            rationale="This term appears in multiple contexts...",
            target_audience="practitioners, academics, general readers"
        )
    ]
    mock_llm.with_structured_output.return_value = mock_structured_output
    
    # Run function
    result = standardize_terminology(["Example"])
    
    # Verify result
    self.assertEqual(result[0]['standard_translation'], "awakening mind")
```

## Error Handling Implementation

### Exception Hierarchy

The system uses a flat exception structure, relying on Python's built-in exceptions:

- `json.JSONDecodeError`: For JSON parsing issues
- `Exception`: For general errors

### Logging Levels

Different log levels are used for different purposes:

- `DEBUG`: Detailed information, useful for debugging
- `INFO`: General information about progress
- `WARNING`: Potential issues that don't stop processing
- `ERROR`: Errors that affect individual items but allow continuation
- `CRITICAL`: Fatal errors that stop processing

### Fallback Strategy

The system implements a three-level fallback strategy:

1. **Batch Retry**: Retry the entire batch once
2. **Individual Processing**: If batch retry fails, process items individually
3. **Content Fallback**: If individual processing fails, keep original content

### Example Error Handling

```python
try:
    # Main logic
    result = process_batch(batch)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    
    try:
        # Retry logic
        result = process_batch(batch)
    except Exception as retry_e:
        logger.error(f"Retry failed: {str(retry_e)}")
        
        # Fallback to defaults
        result = fallback_value
```

## Conclusion

This technical reference provides detailed information about the implementation of the post-translation system. Use it alongside the conceptual overview (`POST_TRANSLATION.md`) for a complete understanding of the system.