# Post-Translation Processing System

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [System Architecture](#system-architecture)
4. [Data Flow](#data-flow)
5. [Key Components](#key-components)
   - [Term Frequency Analysis](#term-frequency-analysis)
   - [Standardization Examples Generation](#standardization-examples-generation)
   - [Terminology Standardization](#terminology-standardization)
   - [Standardized Translation Application](#standardized-translation-application) 
   - [Word-by-Word Translation Generation](#word-by-word-translation-generation)
6. [Input & Output Formats](#input--output-formats)
7. [Multilingual Support](#multilingual-support)
8. [Error Handling & Robustness](#error-handling--robustness)
9. [Performance Considerations](#performance-considerations)
10. [Extension & Customization](#extension--customization)
11. [Command-Line Interface](#command-line-interface)
12. [Common Issues & Solutions](#common-issues--solutions)
13. [Future Improvements](#future-improvements)

## Overview

The post-translation processing system is designed to enhance and standardize translations across a corpus of Tibetan Buddhist texts. It addresses several critical needs:

1. **Terminology Consistency**: Ensuring Tibetan terms are translated consistently throughout the corpus
2. **Final Polishing**: Applying standardized terminology to improve translation quality
3. **Detailed Mapping**: Creating word-by-word translations for language learning and research
4. **Multilingual Support**: Processing translations in multiple target languages

The system works on a corpus level rather than individual documents, analyzing patterns across all translations to identify optimal terminology choices.

## Core Concepts

### Terminology Standardization

When translating from Tibetan to another language, it's common for the same Tibetan term to be translated differently across documents, especially when multiple translators are involved. The standardization process identifies terms with multiple translation variants and selects the best one based on context, frequency, and cross-document compatibility.

### Word-by-Word Translation

Word-by-word translation provides a mapping between each Tibetan word/phrase and its translation in the target language. This is valuable for language learning, textual analysis, and understanding the relationship between the source and target languages.

### Corpus-Based Processing

Unlike document-level translation, post-processing requires analyzing patterns across the entire corpus. This allows the system to make informed decisions based on how terms are used in different contexts.

## System Architecture

The post-translation system is architected as a pipeline with distinct stages:

```
                       ┌─────────────────────────┐
                       │ Corpus of Translations  │
                       └──────────────┬──────────┘
                                      │
                                      ▼
                       ┌─────────────────────────┐
                       │ Term Frequency Analysis │
                       └──────────────┬──────────┘
                                      │
                                      ▼
                       ┌─────────────────────────┐
                       │ Generate Standardization│
                       │      Examples           │
                       └──────────────┬──────────┘
                                      │
                                      ▼
                       ┌─────────────────────────┐
                       │ Standardize Terminology │
                       └──────────────┬──────────┘
                                      │
                                      ▼
                       ┌─────────────────────────┐
                       │ Apply Standardized Terms│
                       └──────────────┬──────────┘
                                      │
                                      ▼
                       ┌─────────────────────────┐
                       │ Generate Word-by-Word   │
                       │    Translations         │
                       └──────────────┬──────────┘
                                      │
                                      ▼
                       ┌─────────────────────────┐
                       │ Output Processed Corpus │
                       └─────────────────────────┘
```

Each stage is implemented as a separate function in `post_translation.py`, allowing for modular testing and extension.

## Data Flow

Data flows through the system in the following manner:

1. **Input**: Corpus of documents with Tibetan source text and translations
2. **Analysis**: Terms and their translations are extracted and analyzed
3. **Decision**: Best translations for each term are selected
4. **Application**: Standardized terms are applied to all documents
5. **Enhancement**: Word-by-word translations are generated
6. **Output**: Finalized corpus and standardized glossary are saved

At each stage, the system maintains data integrity while transforming and enhancing the content.

## Key Components

### Term Frequency Analysis

**Function**: `analyze_term_frequencies()`

This component:
- Extracts all Tibetan terms and their translations from the corpus
- Counts how frequently each Tibetan term is translated in different ways
- Creates a frequency map for each term and its translation variants
- Identifies terms with multiple translation options

**Key Implementation Details**:
- Uses dictionary tracking with term → translation → count structure
- Handles edge cases like empty terms or translations
- Creates a DataFrame with columns: tibetan_term, translation_freq, translation_count
- Sorts translations by frequency for each term

**Example Output**:
```
Tibetan Term: བྱང་ཆུབ་སེམས
Translation Frequencies: bodhicitta (5); awakening mind (3); mind of enlightenment (1)
Translation Count: 3
```

### Standardization Examples Generation

**Function**: `generate_standardization_examples()`

This component:
- Focuses on terms that have multiple translation variants
- Collects usage examples from the corpus for each term
- Creates a detailed standardization prompt for each term
- Limits examples per term to prevent context overload

**Key Implementation Details**:
- Filters terms by translation_count > 1
- Searches for source texts containing the term
- Limits to max_samples_per_term examples
- Includes Sanskrit text when available
- Constructs a standardization protocol customized to the target language

**Example Prompt Structure**:
```
Usage examples:

Sanskrit: bodhicittadruma sadā
Source: བྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་།
Translation: The tree of bodhicitta constantly produces fruit.

Tibetan Term: བྱང་ཆུབ་སེམས 
Translation: bodhicitta (5), awakening mind (3), mind of enlightenment (1)

Translation Standardization Protocol for [Language]:
[Detailed protocol instructions...]
```

### Terminology Standardization

**Function**: `standardize_terminology()`

This component:
- Uses LLM-powered decision making to select the best translation
- Applies a consistent protocol across all terms
- Handles batched processing for performance
- Records standardization rationales

**Key Implementation Details**:
- Uses Pydantic model (WordStandardization) for structured output
- Processes in batches with retry logic
- Logs standardized terms for debugging
- Ensures outputs are in the target language
- Handles fallback to individual processing when batch fails

**Example Output**:
```json
{
  "tibetan_term": "བྱང་ཆུབ་སེམས",
  "standard_translation": "awakening mind",
  "rationale": "This term appears in multiple contexts and 'awakening mind' is more universally applicable in English.",
  "target_audience": "practitioners, academics, general readers"
}
```

### Standardized Translation Application

**Function**: `apply_standardized_terms()`

This component:
- Identifies documents containing standardizable terms
- Creates document-specific glossaries
- Generates prompts for standardization
- Applies the changes while preserving meaning and flow

**Key Implementation Details**:
- Tracks which documents contain which terms
- Handles translation formats (string, list, JSON string)
- Always uses the last/final translation when multiple exist
- Preserves the original translation as plaintext_translation
- Processes in batches with comprehensive error handling

**Key Processing Logic**:
1. Find all Tibetan terms in each document
2. Create a document-specific glossary with standardized terms
3. Process the document with the LLM to apply standardized terms
4. Update the document with the standardized translation

### Word-by-Word Translation Generation

**Function**: `generate_word_by_word()`

This component:
- Creates detailed mappings from Tibetan words to target language
- Handles complex formatting and structure
- Ensures output is in the target language
- Integrates with standardized translations

**Key Implementation Details**:
- Uses standardized translations for consistency
- Provides language-specific examples in the prompt
- Handles multiple input formats (string, list, JSON)
- Uses batched processing with fallbacks
- Auto-inserts language-specific examples (e.g., Chinese examples for Chinese output)

**Example Output Format**:
```
བྱང་ཆུབ་སེམས་དཔའ་ → bodhisattva
སྒོམ་པ་ → meditation
ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་ → perfection of wisdom
རྣམ་པར་ཤེས་པ་ → consciousness
```

## Input & Output Formats

### Input Format

The system accepts a corpus of documents with the following key fields:

- `source`: Tibetan source text
- `translation`: Translation (string, list, or JSON string)
- `sanskrit`: Sanskrit text (optional)
- `combined_commentary`: Commentary (optional)
- `glossary`: List of glossary entries (optional)
- `language`: Target language (optional, auto-detected if not provided)

**Translation Formats Supported**:
1. **String**: Simple translation text
2. **List**: Multiple translation versions (latest will be used)
3. **JSON String**: Serialized list or object containing translations

### Output Format

The system produces two main outputs:

1. **Processed Corpus**: JSONL file with standardized translations
   - Contains required fields: source, translation, combined_commentary, word_by_word_translation, plaintext_translation
   - Translation field contains standardized translation
   - plaintext_translation preserves original translation
   - word_by_word_translation contains the Tibetan-to-target-language mapping

2. **Standardized Glossary**: CSV file with standardized terminology
   - Contains tibetan_term, standard_translation, rationale, target_audience
   - Provides documentation of terminology decisions
   - Can be used for future translation work

**Naming Convention**:
- Corpus: `[input_name]_final.jsonl`
- Glossary: Customizable, default is `standard_translation.csv`

## Multilingual Support

The system supports multiple target languages with several language detection mechanisms:

### Language Detection

1. **Document Field**: Uses `language` field from corpus documents
2. **Filename Detection**: Detects language from input filename (e.g., "english_" or "chinese_")
3. **Command Line**: Accepts explicit language parameter
4. **Default Fallback**: Uses English if no language is detected

### Language-Specific Processing

For each target language:
- Standardized terminology is generated in that language
- Word-by-word translations use appropriate language-specific terms
- Prompts include language-specific instructions
- Examples are customized (e.g., Chinese examples for Chinese output)

### Supported Languages

The system includes built-in support for:
- English
- Chinese
- Spanish
- French
- German
- Japanese
- Hindi
- Russian
- Arabic

Adding new languages requires minimal code changes and primarily involves updating the language detection logic.

## Error Handling & Robustness

The system implements multiple levels of error handling:

### Input Format Handling

- Detects and parses JSON strings
- Handles input where translation is a list
- Extracts the appropriate translation version
- Provides fallbacks for unexpected formats

### Batch Processing with Retries

- Processes documents in batches for performance
- Implements multi-level retry logic:
  1. Batch retry
  2. Individual document retry
  3. Graceful fallback to original content

### Comprehensive Logging

- Detailed debug logs to file
- User-friendly console output
- Clear error messages
- Progress tracking with tqdm
- Language detection reporting

### Data Validation

- Ensures required fields exist
- Handles missing or empty fields
- Validates standardized terms
- Checks for language consistency

## Performance Considerations

### Batch Processing

The system processes documents in batches to optimize LLM API usage:
- Default batch size: 20-30 documents
- Configurable through code
- Automatic parallelization of compatible operations

### Resource Usage

- **Memory**: Scales with corpus size, but processes in chunks
- **API Calls**: Optimized to minimize LLM calls
- **Disk**: Minimal disk usage beyond input/output files

### Optimization Tips

1. **Batch Size Tuning**: Adjust batch size based on document complexity
2. **Example Limiting**: Modify max_samples_per_term for performance vs. quality trade-off
3. **Selective Processing**: Only process documents with standardizable terms

## Extension & Customization

The system is designed for extension in several ways:

### Adding New Languages

1. Update language detection in `examples/post_translation_example.py`
2. Add language-specific examples in prompts if needed
3. Test with sample documents in the new language

### Modifying Standardization Protocol

The standardization protocol is defined in:
```python
def generate_standardization_examples()
```

Modify the protocol text to change how terms are standardized.

### Custom Output Formats

To change output formats:
1. Modify the required_fields list in post_process_corpus
2. Update the output file writing logic for different formats
3. Add new output fields as needed

### Adding New Processing Steps

New processing steps can be added to the pipeline by:
1. Creating a new function for the step
2. Adding it to the post_process_corpus function
3. Ensuring proper data flow between steps

## Command-Line Interface

The system provides a command-line interface through `examples/post_translation_example.py`:

### Basic Usage

```bash
python examples/post_translation_example.py --input corpus.jsonl
```

### Options

- `--input FILE`: Input corpus file (JSON or JSONL)
- `--output FILE`: Output corpus file (default: [input_name]_final.jsonl)
- `--glossary FILE`: Output glossary file (default: standard_translation.csv)
- `--language LANG`: Target language (optional)
- `--sample`: Run with sample data
- `--force`: Continue processing despite errors
- `--debug`: Enable detailed debug logs

### Examples

Process with auto-detected language:
```bash
python examples/post_translation_example.py --input english_corpus.jsonl
```

Specify language explicitly:
```bash
python examples/post_translation_example.py --input corpus.jsonl --language Chinese
```

Custom output locations:
```bash
python examples/post_translation_example.py --input corpus.jsonl --output final_results.jsonl --glossary terms.csv
```

## Common Issues & Solutions

### Issue: Inconsistent Language in Output

**Symptoms**:
- Mixed language in word-by-word translations
- English terms in non-English output

**Solutions**:
1. Check language detection is working correctly
2. Verify corpus documents have consistent language field
3. Use explicit language parameter to override auto-detection
4. Check for English defaults in prompts

### Issue: Missing Word-by-Word Translations

**Symptoms**:
- Empty word_by_word_translation field
- Incomplete mappings

**Solutions**:
1. Check debug logs for LLM errors
2. Ensure translation field is not empty
3. Try processing documents individually
4. Check if LLM is following the specified format

### Issue: JSON Parsing Errors

**Symptoms**:
- Errors with JSON string processing
- Invalid JSON in output

**Solutions**:
1. Check input document format
2. Review debug logs for parsing details
3. Use the `--force` flag to continue despite errors
4. Manually correct problematic documents

### Issue: Slow Processing

**Symptoms**:
- Long processing times
- Timeouts during batch processing

**Solutions**:
1. Reduce batch size
2. Limit max_samples_per_term
3. Process smaller corpus chunks
4. Check for large documents slowing down processing

## Future Improvements

### Short-Term Improvements

1. **Parallel Processing**: Implement true parallel processing for independent operations
2. **Incremental Processing**: Allow resuming interrupted processing
3. **Quality Metrics**: Add evaluation of standardization quality
4. **Term Relationships**: Consider term relationships when standardizing

### Medium-Term Improvements

1. **User Interface**: Add web-based UI for monitoring and control
2. **Terminology Database**: Create persistent terminology database
3. **Pre-trained Models**: Develop specialized models for word-by-word translation
4. **Context Vectorization**: Use embeddings for better context matching

### Long-Term Vision

1. **Self-Improving System**: Learn from human feedback on standardization
2. **Cross-Language Consistency**: Ensure terminology consistency across target languages
3. **Specialized Term Domains**: Support domain-specific terminology sets
4. **Real-time Collaboration**: Enable multiple translators to work with standardized terms

## Conclusion

The post-translation system provides a robust framework for standardizing terminology, enhancing translations, and generating detailed word-by-word mappings. By processing at the corpus level, it ensures consistency across documents while respecting the nuances of each target language.

Future development should focus on improving performance, adding quality metrics, and enhancing the user experience while maintaining the core principles of terminology consistency and linguistic accuracy.