# Tibetan Translator System Documentation

## Overview

The Tibetan Translator is an advanced machine learning based translation system specifically designed to translate and interpret Tibetan Buddhist texts. It employs a multi-stage workflow using LangGraph and LLMs (specifically Claude by Anthropic) to create accurate, contextually appropriate translations that respect the nuances of Buddhist philosophical concepts.

## System Architecture

The system is built as a directed graph workflow, where each node in the graph represents a specific processing step. The workflow processes texts through these steps in a specific order, with conditional branching based on quality evaluations.

### Core Components

1. **Configuration (`config.py`)**
   - Manages environment variables and API keys
   - Defines constants for model settings, file paths, and processing parameters
   - Loads API keys from `.env` file using python-dotenv

2. **Data Models (`models.py`)**
   - Defines Pydantic models and TypedDict for structured data handling
   - Key models include:
     - `State`: The main state object that tracks the entire translation process
     - `CommentaryVerification`: For validating translation against commentary
     - `GlossaryEntry`: For structured glossary term extraction
     - `Feedback`: For structured quality evaluation
     - `Translation`: For formatting and extraction of translations
     - `KeyPoint`: For representing important commentary concepts

3. **Utilities (`utils.py`)**
   - Initializes the LLM client with API keys
   - Provides helper functions for data handling and I/O operations
   - Contains functions for converting between formats (dict to text, state to JSONL)

4. **CLI Interface (`cli.py`)**
   - Provides command-line interface for running the translation pipeline
   - Handles batch processing of multiple translation tasks
   - Manages I/O for translation files

5. **Workflow Definition (`workflow.py`)**
   - Defines the directed graph of the translation workflow
   - Connects processing nodes with appropriate edges
   - Adds conditional routing based on translation quality and formatting status

6. **Prompts (`prompts.py`)**
   - Contains template functions for generating structured prompts to the LLM
   - Standardizes prompt formatting for consistency across the application
   - Includes specialized prompts for each step (translation, evaluation, glossary extraction, etc.)

### Processor Modules

The system is organized into specialized processor modules that handle specific aspects of the translation workflow:

1. **Commentary Processing (`processors/commentary.py`)**
   - Translates commentaries from up to three different sources
   - Extracts key points from commentaries for guiding translation
   - Aggregates commentaries to produce a comprehensive interpretation

2. **Translation Processing (`processors/translation.py`)**
   - Generates initial translations based on source text and commentaries
   - Improves translations based on feedback
   - Routes translations based on quality evaluation

3. **Evaluation Processing (`processors/evaluation.py`)**
   - Verifies translations against commentary key points
   - Evaluates translation quality with structured feedback
   - Routes translations based on evaluation results

4. **Formatting Processing (`processors/formatting.py`)**
   - Ensures translations maintain appropriate formatting
   - Evaluates formatting quality with structured feedback
   - Fixes formatting issues when detected

5. **Glossary Processing (`processors/glossary.py`)**
   - Extracts technical terms and their translations
   - Saves glossary entries to CSV for reference
   - Builds a terminology database across multiple translations

## Translation Workflow Process

The workflow processes a Tibetan text through the following steps:

1. **Commentary Translation**
   - Up to three commentaries are translated in parallel
   - Each commentary provides different perspectives on the text

2. **Commentary Aggregation**
   - Commentaries are combined to create a comprehensive interpretation
   - Key points are extracted to guide translation

3. **Initial Translation**
   - A draft translation is generated based on source text and commentary
   - Structured with consideration for formatting, terminology, and context

4. **Translation Evaluation**
   - The translation is evaluated against commentary key points
   - Graded on a scale from "bad" to "great"
   - Detailed feedback is provided for improvements

5. **Translation Improvement Loop**
   - If the translation is not satisfactory, it returns to the translation generator
   - Incorporates feedback for iterative improvement
   - Continues until quality reaches "great" or maximum iterations (4) is reached

6. **Format Evaluation**
   - Ensures translation preserves source text's formatting
   - Provides specific formatting feedback if needed

7. **Format Correction Loop**
   - If formatting is not satisfactory, applies formatting fixes
   - Continues until formatting is correct or maximum iterations (6) is reached

8. **Glossary Extraction**
   - Extracts key terms and their translations
   - Produces a glossary CSV file for reference

## Data Flow

1. **Input Data**
   - Source Tibetan text
   - Sanskrit equivalent (if available)
   - Commentaries (up to three)

2. **State Management**
   - The `State` object tracks the entire translation process
   - Contains translations, commentaries, feedback, and metadata
   - Passed between processing nodes with updates

3. **Output Data**
   - Final translation
   - Formatting-corrected translation
   - Extracted glossary
   - Translation history with feedback

## Usage

### Basic Usage

```python
from tibetan_translator import optimizer_workflow

# Initialize the workflow with a Tibetan text
state = optimizer_workflow.invoke({
    "source": "Tibetan text here...",
    "sanskrit": "Sanskrit equivalent if available...",
    "commentary1": "First commentary...",
    "commentary2": "Second commentary...",
    "commentary3": "Third commentary...",
    "feedback_history": [],
    "format_feedback_history": [],
    "itteration": 0,
    "formated": False,
    "glossary": [],
    "language": "English"
})

# Access the results
final_translation = state["translation"][-1]
glossary_entries = state["glossary"]
```

### Batch Processing

```python
from tibetan_translator.utils import get_json_data
from test_workflow import run_batch_processing

# Load test data
test_data = get_json_data('test_data/test.json')

# Run batch processing
results = run_batch_processing(
    data=test_data,
    batch_size=2,
    run_name="translation_batch"
)
```

### Command Line Interface

```bash
python tibetan_translator/cli.py --input path/to/input.json --output translations.jsonl --batch_size 4 --preprocess
```

## Configuration

The system requires API keys for the Anthropic Claude API. Create a `.env` file in the project root with:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

## Dependencies

- `langchain-anthropic`: For interfacing with Claude API
- `pydantic`: For data validation and structured output
- `typing-extensions`: For advanced type hints
- `tqdm`: For progress bars
- `pandas`: For glossary CSV handling
- `langgraph`: For workflow management
- `python-dotenv`: For environment variable management

## Extension Points

The system is designed to be extended in several ways:

1. **Adding New Processors**
   - Create new processor modules in the `processors/` directory
   - Add them to the workflow graph in `workflow.py`

2. **Customizing Prompts**
   - Modify or add prompts in `prompts.py` to adjust LLM behavior

3. **Supporting New Languages**
   - Update the `language` parameter in the State object
   - Adjust prompts for the target language

4. **Adding Post-Processing Steps**
   - Add new nodes to the workflow graph after the glossary extraction