# Tibetan Translator

## Overview

Tibetan Translator is a comprehensive system for translating Tibetan Buddhist texts into multiple languages. It employs a multi-stage agentic workflow using LangGraph and Large Language Models to create accurate, contextually appropriate translations that respect the nuances of Buddhist philosophical concepts.

## Features

* **Traditional Commentary Integration**: Leverages traditional commentaries to guide translation when available
* **Source-Focused Translation**: Provides direct translation with linguistic analysis when commentaries aren't available
* **Multi-language Support**: Translates into multiple target languages (English, Chinese, Hindi, etc.)
* **Glossary Generation**: Automatically extracts key terms with consistent translations
* **Quality Evaluation**: Iteratively improves translations through feedback loops
* **Post-Translation Processing**: Standardizes terminology across a corpus of translations
* **Word-by-Word Translation**: Generates detailed mappings between Tibetan and target language
* **Batch Processing**: Handles multiple texts with comprehensive error recovery

## Project Structure

```
├── README.md                # Project documentation
├── setup.py                 # Package setup script
├── requirements.txt         # Dependencies
├── tibetan_translator/      # Main package
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration settings
│   ├── models.py            # Model definitions
│   ├── prompts.py           # Predefined LLM prompts
│   ├── processors/          # Processing modules
│   │   ├── __init__.py      # Processor module initialization
│   │   ├── commentary.py    # Commentary translation processing
│   │   ├── translation.py   # Translation handling
│   │   ├── evaluation.py    # Evaluation and verification
│   │   ├── formatting.py    # Formatting adjustments
│   │   ├── glossary.py      # Glossary extraction
│   │   └── post_translation.py # Post-translation processing
│   ├── workflow.py          # Main translation workflow
│   ├── utils.py             # Utility functions
│   └── cli.py               # Command-line interface
├── doc/                     # Documentation
│   ├── SYSTEM_OVERVIEW.md   # High-level architecture
│   ├── USAGE_GUIDE.md       # Usage instructions
│   ├── MODULE_DETAILS.md    # Technical component docs
│   ├── POST_TRANSLATION.md  # Post-translation guide
│   └── TRANSLATION_WITHOUT_COMMENTARY.md # Non-commentary workflow
├── examples/                # Usage examples
│   ├── basic_usage.py       # Basic usage example
│   ├── batch_processing.py  # Batch processing example
│   ├── post_translation_example.py # Post-translation example
│   └── zero_shot_translator.py # Simpler direct translation
└── tests/                   # Unit tests
```

## Installation

Ensure you have Python installed (>=3.8), then install the dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with your API keys:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
LLM_MODEL_NAME=claude-3-7-sonnet-latest
MAX_TOKENS=5000
```

## Usage

### Basic Translation Workflow

```python
from tibetan_translator import optimizer_workflow

# Initialize the workflow with a Tibetan text
state = optimizer_workflow.invoke({
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
})

# Access the results
final_translation = state["translation"][-1]
plaintext_translation = state["plaintext_translation"]
glossary_entries = state["glossary"]
```

### Command Line Usage

Process single files:

```bash
# Basic translation workflow
python test_workflow.py

# Simple translation (Gemini model)
python simple_translate.py input.json --target-lang Chinese
```

### Batch Processing

```bash
# Process multiple files
python batch_process.py --input test.json --batch-size 5

# Zero-shot batch translation
python examples/zero_shot_translator.py --input file.json --language Hindi
```

### Translation Without Commentary

When commentaries aren't available, the system automatically switches to source-focused mode:

```python
# Initialize with empty commentary fields
state = optimizer_workflow.invoke({
    "source": "ཇི་ལྟར་མཐོང་ཐོས་ཤེས་པ་དག །\nའདིར་ནི་དགག་པར་བྱ་མིན་ཏེ།",
    "commentary1": "",  # Empty commentary
    "commentary2": "",  # Empty commentary
    "commentary3": "",  # Empty commentary
    "language": "English",
})
```

For more details, see [Translation Without Commentary](doc/TRANSLATION_WITHOUT_COMMENTARY.md).

### Post-Translation Processing

Apply terminology standardization and word-by-word translation across a corpus:

```bash
python examples/post_translation_example.py --input corpus.jsonl --language Hindi
```

For detailed post-translation documentation, see [Post-Translation Guide](doc/POST_TRANSLATION.md).

## Examples

The `examples/` directory contains runnable examples:

1. **Basic usage**: Simple translation workflow
   ```
   python examples/basic_usage.py
   ```

2. **Batch processing**: Process multiple texts
   ```
   python examples/batch_processing.py
   ```

3. **Post-translation**: Process a corpus
   ```
   python examples/post_translation_example.py --sample
   ```

4. **Zero-shot**: Simple batch translation
   ```
   python examples/zero_shot_translator.py --input test_data/tibetan_samples.json
   ```

## Testing

Run tests using pytest:

```bash
python -m pytest tests/
```

## Documentation

Comprehensive documentation is available in the `doc/` directory:

- `SYSTEM_OVERVIEW.md`: High-level architecture
- `USAGE_GUIDE.md`: Detailed usage instructions
- `MODULE_DETAILS.md`: Technical documentation
- `POST_TRANSLATION.md`: Post-translation processing
- `TRANSLATION_WITHOUT_COMMENTARY.md`: Non-commentary workflow

## Contributing

Pull requests and contributions are welcome. Please open an issue for discussions.

## License

MIT License