# Index

This folder contains a guide to the documentation for the `agentic_translation` project codebase. 

The structure of this codebase is shown below.

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
|   |   ├── ReadMe.md        # Documents the files in the processors folder
│   │   ├── __init__.py      # Processor module initialization
│   │   ├── commentary.py    # Commentary translation processing
│   │   ├── translation.py   # Translation handling
│   │   ├── evaluation.py    # Evaluation and verification
│   │   ├── formatting.py    # Formatting adjustments
│   │   └── glossary.py      # Glossary extraction
|   ├── ReadMe.md            # Documents the files in the tibetan_translator folder
│   ├── workflow.py          # Main translation workflow
│   ├── utils.py             # Utility functions
│   └── cli.py               # Command-line interface
├── docs/                    # Project documentation
│   ├── Index.md             # Index of documentation
│   ├── Quickstart.md        # Basic usage guide for quickstart
│   ├── TibetanTranslator.md # Documents tibetan_translator folder
│   └── Processors.md        # Documents tibetan_translator/processors subfolder
├── examples/                # Usage examples
│   ├── basic_usage.py       # Basic usage example
│   └── batch_processing.py  # Batch processing example
└── tests/                   # Unit tests
    ├── __init__.py          # Test package initialization
    ├── test_processors.py   # Tests for processors
    ├── test_workflow.py     # Tests for workflow
    └── test_utils.py        # Tests for utility functions
```

## Documentation

This folder contains 4 files: Index.md (this file), Quickstart.md, TibetanTranslator.md, and Processors.md.

### [Quickstart](Quickstart.md)

`Quickstard.md` provides only the necessary information to use the command-line interface for this project.

### [TibetanTranslator](TibetanTranslator.md)

`TibetanTranslator.md` provides comprehensive documentation of the `tibetan_translator` folder and its files. This folder provides the main functionality of this codebase as described in the main ReadMe.

The information in this file is also provided in `tibetan_translator/ReadMe.md`

### [Processors](Processors.md)

`Processors` provides comprehensive documentation for the `processors` subfolder inside `tibetan_translator`. This subfolder defines the structured pipeline utilized by the `tibetan_translator` workflow.
