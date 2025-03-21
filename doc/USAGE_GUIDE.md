# Tibetan Translator: Usage Guide

This document provides comprehensive instructions for using the Tibetan Buddhist Translation System, including how to set up the environment, prepare input data, run translations, and utilize various utility tools.

## Table of Contents

1. [Installation](#installation)
2. [Environment Setup](#environment-setup)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Batch Processing](#batch-processing)
6. [Glossary Generation](#glossary-generation)
7. [Troubleshooting](#troubleshooting)

## Installation

### Requirements

- Python 3.8+
- Required packages (see `requirements.txt`)
- Anthropic API key for Claude 3 access

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tibetan-translator.git
   cd tibetan-translator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up API credentials:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys
   ```

## Environment Setup

### Creating a .env File

Create a `.env` file in the project root with the following contents:

```
ANTHROPIC_API_KEY=your_api_key_here
LLM_MODEL_NAME=claude-3-7-sonnet-latest
MAX_TOKENS=5000
```

### Configure Parameters

Key configuration parameters can be modified in `tibetan_translator/config.py`:

- `MAX_TRANSLATION_ITERATIONS`: Maximum number of refinement iterations
- `MAX_FORMAT_ITERATIONS`: Maximum number of formatting correction iterations
- `LLM_MODEL_NAME`: The Claude model to use (default: claude-3-7-sonnet-latest)
- `MAX_TOKENS`: Maximum token limit for responses

## Basic Usage

### Single Text Translation

To translate a single Tibetan text:

```python
from tibetan_translator import optimizer_workflow
from tibetan_translator.models import State

# Prepare input
input_data = {
    "source": "བཅོམ་ལྡན་འདས་རྒྱལ་པོའི་ཁབ་བྱ་རྒོད་ཕུང་པོའི་རི་ལ་དགེ་སློང་གི་དགེ་འདུན་ཆེན་པོ་དང་།",
    "sanskrit": "भगवान् राजगृहे विहरति स्म गृध्रकूटे पर्वते महता भिक्षुसंघेन",
    "commentary1": "...",  # Optional commentary
    "commentary2": "...",  # Optional commentary
    "commentary3": "...",  # Optional commentary
    "feedback_history": [],
    "format_feedback_history": [],
    "itteration": 0,
    "format_iteration": 0,
    "formated": False,
    "glossary": [],
    "language": "English"  # Target language
}

# Run the workflow
result = optimizer_workflow.invoke(input_data)
print(f"Final translation: {result['translation'][-1]}")
print(f"Plain translation: {result['plaintext_translation']}")
```

### Running Examples

The repository includes several example scripts in the `examples/` directory:

1. Basic Usage:
   ```bash
   python examples/basic_usage.py
   ```

2. Few-shot Examples:
   ```bash
   python examples/few_shot_examples.py
   ```

3. Post-translation Processing:
   ```bash
   python examples/post_translation_example.py
   ```

## Advanced Usage

### Custom Language Support

The system supports translation to any language by changing the `language` parameter:

```python
input_data = {
    # ... other fields ...
    "language": "Italian"  # or French, German, Spanish, etc.
}
```

### Working with Commentaries

Commentary translation is an important part of the system:

1. If you have traditional commentaries, provide them in the `commentary1`, `commentary2`, and `commentary3` fields
2. If you don't have commentaries, you can leave these fields empty or set them to ""
3. The system will automatically generate a combined commentary or create a zero-shot commentary if none exist

Example with partial commentaries:

```python
input_data = {
    # ... other fields ...
    "commentary1": "ཆོས་ཀྱི་ཕུང་པོ་བརྒྱད་ཁྲི་བཞི་སྟོང་གི་འབྱུང་གནས།",
    "commentary2": "",  # Empty commentary
    "commentary3": "འདི་སྐད་བདག་གིས་ཐོས་པ་དུས་གཅིག་ན།",
}
```

### Test Workflow

To test the entire workflow with sample data:

```bash
python test_workflow.py
```

This will process example data through the complete workflow and save results to `test_workflow.jsonl`.

## Batch Processing

### Basic Batch Processing

To process multiple texts in batches:

```bash
python batch_process.py --input test.json --output batch_results
```

### Advanced Batch Processing Options

The batch processor supports multiple options for robust handling:

```bash
python batch_process.py \
  --input test.json \
  --batch-size 3 \
  --retries 4 \
  --delay 10 \
  --language Italian \
  --output italian_results
```

Options:
- `--input`: Input JSON or JSONL file with texts to translate
- `--batch-size`: Number of texts to process in each batch
- `--retries`: Maximum retry attempts for failed batches
- `--delay`: Delay in seconds between retry attempts
- `--language`: Target language for translation
- `--output`: Output file prefix for results

### Input Format

The input JSON file should contain an array of objects with the following structure:

```json
[
  {
    "root_display_text": "བཅོམ་ལྡན་འདས་རྒྱལ་པོའི་ཁབ་བྱ་རྒོད་ཕུང་པོའི་རི་ལ་དགེ་སློང་གི་དགེ་འདུན་ཆེན་པོ་དང་།",
    "sanskrit_text": "भगवान् राजगृहे विहरति स्म गृध्रकूटे पर्वते महता भिक्षुसंघेन",
    "commentary_1": "...",
    "commentary_2": "...",
    "commentary_3": "..."
  },
  // More entries...
]
```

## Glossary Generation

### Standalone Glossary Tool

After processing translations, you can generate a glossary from the result files:

```bash
python generate_glossary.py --input results.jsonl --output glossary.csv
```

For multiple input files:

```bash
python generate_glossary.py --input file1.jsonl file2.jsonl --output combined_glossary.csv
```

### Glossary Output Format

The glossary CSV includes the following columns:
- `tibetan_term`: Original Tibetan term
- `translation`: Translation in target language
- `category`: Term category (philosophical, technical, etc.)
- `context`: Usage context in target language
- `commentary_reference`: Reference to commentary in target language
- `entity_category`: Entity type for names, places, etc.

## Troubleshooting

### Common Issues

1. **Context Window Errors**

   **Problem**: LLM returns errors about exceeding max tokens
   
   **Solution**: 
   - Reduce batch size
   - Use smaller source texts
   - Shorten commentaries if possible
   - Set lower MAX_TOKENS in config.py

2. **Empty or Missing Commentaries**

   **Problem**: No commentaries available for source text
   
   **Solution**:
   - This is handled automatically with zero-shot commentary generation
   - No action needed, the system will adapt

3. **Batch Processing Failures**

   **Problem**: Batch processing fails for certain texts
   
   **Solution**:
   - Use the robust batch processor with retry logic
   - Set higher --retries and --delay values
   - Reduce --batch-size to 1 for difficult texts

4. **API Rate Limits**

   **Problem**: Hitting Anthropic API rate limits
   
   **Solution**:
   - Increase the --delay parameter
   - Process smaller batches
   - Add error handling that respects rate limit headers

### Getting Help

For more detailed troubleshooting:

1. Check the log files in the project directory
2. Run the workflow with debug=True:
   ```python
   result = optimizer_workflow.invoke(input_data, debug=True)
   ```
3. Examine the output JSONL files for specific error messages
4. Consult the API documentation for error codes at [Anthropic API docs](https://docs.anthropic.com/en/api)