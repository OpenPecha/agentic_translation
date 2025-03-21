# Tibetan Translator

## Overview

Tibetan Translator is a structured translation and evaluation pipeline for Tibetan Buddhist texts. It integrates automated workflows for translation, commentary verification, glossary extraction, and formatting.

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
│   │   └── glossary.py      # Glossary extraction
│   ├── workflow.py          # Main translation workflow
│   ├── utils.py             # Utility functions
│   └── cli.py               # Command-line interface
├── examples/                # Usage examples
│   ├── basic_usage.py       # Basic usage example
│   └── batch_processing.py  # Batch processing example
└── tests/                   # Unit tests
    ├── __init__.py          # Test package initialization
    ├── test_processors.py   # Tests for processors
    ├── test_workflow.py     # Tests for workflow
    └── test_utils.py        # Tests for utility functions
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
```

These API keys are required for the LLM models used in translation.

## Usage

Run the CLI tool to process a translation:

```bash
python tibetan_translator/cli.py --input path/to/input.txt --output path/to/output.txt
```

## Features

* **Automated Translation** : Uses LLM to translate Tibetan Buddhist texts.
* **Commentary Verification** : Ensures alignment with key commentary points.
* **Glossary Extraction** : Identifies and extracts key terms.
* **Formatting** : Maintains proper textual structure.
* **Evaluation** : Grades and improves translation iteratively.

## Contributing

Pull requests and contributions are welcome. Please open an issue for discussions.

## License

MIT License![](blob:vscode-webview://0e354hastvqtolcub64vo6m69cahm8uc6d3ajjd1d6b92vblrh85/3a28f53e-bb10-4f1f-ad5a-61f5246e284a)
