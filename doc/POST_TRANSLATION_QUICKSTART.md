# Post-Translation System: Quick Start Guide

This guide provides a quick introduction to the post-translation system, with practical examples to help you get started.

## Overview

The post-translation system enhances a corpus of Tibetan translations by:

1. Creating a standardized glossary of Tibetan terms
2. Applying standardized terminology to all translations
3. Generating word-by-word translations for each document

## Prerequisites

- Python 3.8+
- Required packages: pandas, tqdm, pydantic, langchain
- Anthropic API key set in environment variables

## Installation

No additional installation is required beyond the main Tibetan translator project.

## Basic Usage

### Command Line Interface

The simplest way to use the post-translation system is via the command line:

```bash
# Process a corpus with auto-detected language
python examples/post_translation_example.py --input your_corpus.jsonl

# Process with explicit language
python examples/post_translation_example.py --input your_corpus.jsonl --language Chinese

# Customize output locations
python examples/post_translation_example.py --input your_corpus.jsonl --output custom_output.jsonl --glossary custom_glossary.csv

# Run with sample data
python examples/post_translation_example.py --sample
```

### Input Format

Your input corpus should be a JSON or JSONL file with documents containing:

```json
{
  "source": "བྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་།",
  "translation": "The tree of bodhicitta constantly produces fruit.",
  "sanskrit": "bodhicittadruma sadā",
  "combined_commentary": "The tree of bodhicitta is a metaphor for...",
  "glossary": [
    {
      "tibetan_term": "བྱང་ཆུབ་སེམས",
      "translation": "bodhicitta",
      "context": "The awakening mind",
      "commentary_reference": "From Śāntideva",
      "category": "philosophical",
      "entity_category": ""
    }
  ],
  "language": "English"
}
```

The system supports various translation formats:
- Simple string: `"translation": "The tree of bodhicitta..."`
- List of alternatives: `"translation": ["Version 1", "Version 2", "Final version"]`
- JSON string: `"translation": "[\"Version 1\", \"Version 2\"]"`

### Output Files

The system produces two main outputs:

1. **Processed Corpus**: `[input_name]_final.jsonl`
   ```json
   {
     "source": "བྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་།",
     "translation": "The tree of awakening mind constantly produces fruit.",
     "combined_commentary": "The tree of bodhicitta is a metaphor for...",
     "word_by_word_translation": "བྱང་ཆུབ་སེམས → awakening mind\nལྗོན་ཤིང → tree",
     "plaintext_translation": "The tree of bodhicitta constantly produces fruit."
   }
   ```

2. **Standardized Glossary**: `standard_translation.csv`
   ```csv
   tibetan_term,standard_translation,rationale,target_audience
   བྱང་ཆུབ་སེམས,awakening mind,This term appears in multiple contexts...,practitioners academics general readers
   ```

## Common Use Cases

### 1. Standardizing a Completed Translation Project

```bash
# Assuming you have a corpus of completed translations
python examples/post_translation_example.py --input completed_project.jsonl
```

### 2. Supporting Multiple Languages

```bash
# Chinese translations
python examples/post_translation_example.py --input chinese_corpus.jsonl --language Chinese

# Spanish translations
python examples/post_translation_example.py --input spanish_corpus.jsonl --language Spanish
```

The system will auto-detect the language if:
- Filename contains language hint (e.g., "chinese_corpus.jsonl")
- Documents have a "language" field
- Otherwise, you must specify with --language

### 3. Handling Problematic Files

If you encounter errors during processing:

```bash
# Continue despite errors
python examples/post_translation_example.py --input problematic_corpus.jsonl --force

# Enable detailed debug logging
python examples/post_translation_example.py --input problematic_corpus.jsonl --debug
```

## Programmatic Usage

You can also use the post-translation system from your Python code:

```python
from tibetan_translator.processors.post_translation import post_process_corpus

# Load your corpus (list of document dictionaries)
corpus = [...]

# Process the corpus
processed_corpus = post_process_corpus(
    corpus=corpus,
    output_file="my_output.jsonl",
    glossary_file="my_glossary.csv",
    language="English"  # Optional, auto-detects if not provided
)
```

## Advanced Features

### Customizing Batch Size

For large corpora, you may want to adjust batch size inside `post_translation.py`:

```python
# For standardize_terminology
batch_size = 30  # Default

# For generate_word_by_word
batch_size = 20  # Default
```

### Limiting Examples Per Term

To improve performance, you can limit the number of examples used for standardization:

```python
# In post_process_corpus function
examples = generate_standardization_examples(
    term_freq_df, 
    corpus, 
    max_samples_per_term=10,  # Default is 20
    language=language
)
```

## Troubleshooting

### Issue: Missing Word-by-Word Translations

**Solution**: Check debug logs (with --debug flag) for LLM errors. Try processing a smaller corpus.

### Issue: Inconsistent Language in Output

**Solution**: Explicitly specify language with --language parameter.

### Issue: Slow Processing

**Solution**: 
1. Reduce batch size in code
2. Process smaller corpus chunks
3. Limit max_samples_per_term

### Issue: JSON Parsing Errors

**Solution**: 
1. Check input file format
2. Use --force flag to continue despite errors
3. Check debug logs for details

## Getting Help

For more detailed information, refer to:
- `POST_TRANSLATION.md`: Conceptual overview
- `POST_TRANSLATION_CODE_REFERENCE.md`: Technical reference