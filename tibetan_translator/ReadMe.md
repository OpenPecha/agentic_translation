# Tibetan Translator

This folder is composed of seven files, excluding this ReadMe, and one subfolder, `processors`. The files are listed below as links to the relevant section in this ReadMe. Each section header is also a link to the relevant source code, with the exception of 'processors' which link to its relevant ReadMe file.

## Contents
1. **[\_\_init__.py](#__init__py)**
2. **[cli.py](#clipy)**
3. **[config.py](#configpy)**
4. **[models.py](#modelspy)**
5. **[prompts.py](#promptspy)**
6. **[utils.py](#utilspy)**
7. **[workflow.py](#workflowpy)**

## [processors](processors/ReadMe.md)

These files provide a structured pipeline for translating Tibetan texts with commentary integration, evaluation, and refinement. It includes:

- **Commentary Processing ([commentary.py](processors/ReadMe.md#commentarypy))** – Extracts key points and translates thematic commentaries.
- **Translation Generation ([translation.py](processors/ReadMe.md#translationpy))** – Produces and iteratively improves translations.
- **Evaluation & Verification ([evaluation.py](processors/ReadMe.md#evaluationpy))** – Assesses translation accuracy against commentaries.
- **Formatting ([formatting.py](processors/ReadMe.md#formattingpy))** – Ensures structural fidelity to the source text.
- **Glossary Extraction ([glossary.py](processors/ReadMe.md#glossarypy))** – Identifies key terms for a structured glossary.

## [\_\_init__.py](__init__.py)

The `__init__.py` file defines the public interface for the `tibetan_translator` package by importing essential modules and functions.

#### Key Imports
- **Configuration**: `tibetan_translator.config`
- **Utilities**: `tibetan_translator.utils`
- **Workflow**: `tibetan_translator.workflow.optimizer_workflow`
- **Processors**: Functions for **commentary**, **translation**, **evaluation**, **formatting**, and **glossary**.

#### Public API
The `__all__` list specifies the publicly available components:

```python
__all__ = [
    "optimizer_workflow",
    "commentary",
    "translation",
    "evaluation",
    "formatting",
    "glossary"
]
```

This allows direct access to the core components when importing the package. For example:

```python
from tibetan_translator import optimizer_workflow, commentary, translation
```

## [cli.py](cli.py)

The `cli.py` file defines a command-line interface (CLI) for running the Tibetan translation workflow. It allows users to process translation data from an input file, apply the workflow in batches, and save the results in an output file. The steps of this process are as follows:

### **Execution Steps**

1. **Preprocessing**: 
   - If `--preprocess` is provided, the input data is transformed into a format suitable for the translation workflow. This involves creating dictionaries for each data entry, which are then processed in batches.

2. **Batch Processing**: 
   - The data is processed in batches, as defined by the `batch_size` argument. Each batch is processed through the translation workflow, and the results are saved in a JSONL file.

3. **Error Handling**: 
   - If an error occurs during batch processing, the failed data entries are saved in a separate failure file (`{run_name}_fail.jsonl`).

4. **Result Saving**: 
   - After processing, the results are saved in the specified output file (`{run_name}.jsonl`).

### Expected Input and Output Structure

#### Input
The input data is expected to be in **JSON format**. Each entry in the input file represents a translation task and should contain several key fields. The expected structure for the input file (e.g., `input_data.json`) is shown below.

##### **Input JSON Structure**
```json
[
    {
        "root": "Tibetan root text or sentence",
        "sanskrit": "Corresponding Sanskrit text",
        "commentary_1": "Optional commentary 1",
        "commentary_2": "Optional commentary 2",
        "commentary_3": "Optional commentary 3",
        "feedback_history": [],
        "format_feedback_history": [],
        "itteration": 0,
        "formated": false,
        "glossary": [],
        "language": "English"
    },
    {
        "root": "Another Tibetan root text or sentence",
        "sanskrit": "Corresponding Sanskrit text",
        "commentary_1": "Another optional commentary 1",
        "commentary_2": "Another optional commentary 2",
        "commentary_3": "Another optional commentary 3",
        "feedback_history": [],
        "format_feedback_history": [],
        "itteration": 0,
        "formated": false,
        "glossary": [],
        "language": "English"
    }
]
```

##### Key Fields
- **`root`**: The original Tibetan text (root text) that is to be translated.
- **`sanskrit`**: The corresponding Sanskrit text.
- **`commentary_1`, `commentary_2`, `commentary_3`**: Optional commentaries (typically used to give more context for the translation).
- **`feedback_history`**: A list that holds feedback entries on previous translations.
- **`format_feedback_history`**: A list that holds feedback specifically related to the formatting of the translation.
- **`itteration`**: A counter to keep track of the number of translation iterations. This can be used to track the evolution of a translation over time.
- **`formated`**: A boolean indicating whether the translation has been formatted correctly.
- **`glossary`**: A list of glossary entries (if applicable) for the current translation.
- **`language`**: The language to which the translation should be made (typically "English").

Each entry corresponds to one translation task, and you may have multiple entries in the input JSON array.

#### Output

The output of the translation process will be a **JSONL (JSON Lines)** format file, where each line is a JSON object representing the state of a translation task after processing. The structure of the output will be similar to the input, but with additional data generated as part of the workflow, including translations, commentary analysis, formatting feedback, and glossary entries.

##### **Output JSONL Structure**
```json
{
    "translation": ["English translation of the Tibetan text"],
    "commentary1_translation": "Translation of commentary 1",
    "commentary2_translation": "Translation of commentary 2",
    "commentary3_translation": "Translation of commentary 3",
    "source": "Tibetan root text or sentence",
    "sanskrit": "Sanskrit translation of the text",
    "language": "English",
    "feedback_history": ["Feedback on translation step 1", "Feedback on translation step 2"],
    "format_feedback_history": ["Feedback on formatting step 1", "Feedback on formatting step 2"],
    "commentary1": "Original commentary 1 text",
    "commentary2": "Original commentary 2 text",
    "commentary3": "Original commentary 3 text",
    "combined_commentary": "Combined commentary from all sources",
    "key_points": [
        {
            "concept": "Core concept 1",
            "terminology": ["Term1", "Term2"],
            "context": "Context or explanation of the concept",
            "implications": ["Implication 1", "Implication 2"]
        },
        {
            "concept": "Core concept 2",
            "terminology": ["Term3", "Term4"],
            "context": "Context or explanation of the concept",
            "implications": ["Implication 3", "Implication 4"]
        }
    ],
    "itteration": 1,
    "formated": true,
    "glossary": [
        {
            "tibetan_term": "Tibetan term 1",
            "translation": "English translation of the term",
            "context": "Context or usage note",
            "entity_category": "Entity category (if applicable)",
            "commentary_reference": "Reference to commentary explanation",
            "category": "Category (e.g., philosophical, technical)"
        }
    ],
    "plaintext_translation": "Plain text translation of the Tibetan source"
}
```

##### Key Fields
- **`translation`**: The English translation of the Tibetan source text.
- **`commentary1_translation`, `commentary2_translation`, `commentary3_translation`**: Translations for each of the three commentary sections.
- **`source`**: The original Tibetan root text.
- **`sanskrit`**: The Sanskrit translation of the source.
- **`feedback_history`**: A list of feedback regarding the translation process.
- **`format_feedback_history`**: A list of feedback regarding the formatting of the translation.
- **`commentary1`, `commentary2`, `commentary3`**: The original commentary text for each section.
- **`combined_commentary`**: A combined text containing all three commentaries.
- **`key_points`**: A list of key concepts or interpretations derived from the commentary, along with the terminology, context, and implications.
- **`itteration`**: The iteration count for this translation task.
- **`formated`**: A boolean indicating whether the translation has been formatted.
- **`glossary`**: A list of glossary entries, each containing a Tibetan term and its English translation, with context, category, and commentary references.
- **`plaintext_translation`**: The plain text (non-formatted) translation of the Tibetan source text.

### Example Input and Output

#### Example Input

```json
[
    {
        "root": "བོད་ཀྱི་བསྡུད་མ་འདུག",
        "sanskrit": "Buddhist text in Sanskrit",
        "commentary_1": "Commentary 1 explanation",
        "commentary_2": "Commentary 2 explanation",
        "commentary_3": "Commentary 3 explanation",
        "feedback_history": [],
        "format_feedback_history": [],
        "itteration": 0,
        "formated": false,
        "glossary": [],
        "language": "English"
    }
]
```

#### Example Output (in JSONL format)

```json
{
    "translation": ["There is no suffering in Tibetan Buddhism"],
    "commentary1_translation": "Translation of Commentary 1",
    "commentary2_translation": "Translation of Commentary 2",
    "commentary3_translation": "Translation of Commentary 3",
    "source": "བོད་ཀྱི་བསྡུད་མ་འདུག",
    "sanskrit": "Buddhist text in Sanskrit",
    "language": "English",
    "feedback_history": ["Feedback on translation step 1"],
    "format_feedback_history": ["Feedback on formatting step 1"],
    "commentary1": "Commentary 1 explanation",
    "commentary2": "Commentary 2 explanation",
    "commentary3": "Commentary 3 explanation",
    "combined_commentary": "Combined commentary text",
    "key_points": [
        {
            "concept": "Suffering",
            "terminology": ["duḥkha"],
            "context": "Philosophical context of suffering in Buddhism",
            "implications": ["Implication 1", "Implication 2"]
        }
    ],
    "itteration": 1,
    "formated": true,
    "glossary": [
        {
            "tibetan_term": "སྡུད",
            "translation": "suffering",
            "context": "Used in the context of Buddhist philosophy",
            "entity_category": "Philosophical term",
            "commentary_reference": "Commentary 1",
            "category": "Philosophical"
        }
    ],
    "plaintext_translation": "No suffering in Tibetan Buddhism"
}
```

This output reflects a fully processed translation task, including commentary translations, key points, glossary entries, and formatted text.

### **Key Components**

1. **`run` function**:
   - **Purpose**: This is the core function that processes the translation workflow.
   - **Arguments**:
     - `data`: A list of dictionaries containing the translation data.
     - `batch_size`: The number of records to process in each batch.
     - `run_name`: The name used for saving the output files.
     - `preprocess`: A flag indicating whether to preprocess the data before running the workflow.
   - **Process**:
     - If `preprocess` is `True`, the function constructs input dictionaries from the data.
     - The data is split into batches (using `batch_size`), and the workflow is applied to each batch using `optimizer_workflow.batch(batch)`.
     - The results are saved in a JSONL file using `convert_state_to_jsonl()`.
     - If any error occurs, it saves the failed data in a separate file.

2. **`run_translation_pipeline` function**:
   - **Purpose**: This function handles reading the input data and saving the results after running the translation pipeline.
   - **Arguments**:
     - `input_file`: The path to the input JSON file containing the translation data.
     - `output_file`: The path to the output JSONL file where results will be saved.
     - `batch_size`: The batch size for processing.
     - `preprocess`: Whether to preprocess the data.
   - **Process**:
     - It loads the input data using `get_json_data(input_file)`.
     - Then, it calls the `run()` function to process the data and save the results.

3. **`main` function**:
   - **Purpose**: The entry point for the CLI, which sets up argument parsing and runs the translation pipeline.
   - **Arguments**:
     - `--input`: The path to the input JSON file (required).
     - `--output`: The path to the output JSONL file (required).
     - `--batch_size`: The batch size for processing (default: 4).
     - `--preprocess`: A flag indicating whether to preprocess the data before running the workflow.
   - **Process**:
     - The function parses the command-line arguments and calls `run_translation_pipeline()` to process the input data.

### **Usage Example**

```bash
python cli.py --input input_data.json --output output_results.jsonl --batch_size 8 --preprocess
```

This will:
- Read data from `input_data.json`.
- Process the data in batches of 8.
- Preprocess the data before running the translation workflow.
- Save the results in `output_results.jsonl`.

## [config.py](config.py)

The config.py file defines configuration settings for the translation process, including API keys, model settings, file paths, and translation parameters. It sets up environment variables, model options, file paths for glossary and state storage, and translation and formatting settings.
Key Components

- **API Configuration**: Loads the API key for accessing external services, prompting the user to enter the key securely.
- **Model Configuration**: Specifies the language model (claude-3-5-sonnet-latest) and maximum token limit for text processing.
- **File Paths**: Defines the file locations for storing the glossary (translation_glossary.csv) and translation states (translation_states.jsonl).
- **Translation Settings**: Sets the maximum number of iterations (MAX_ITERATIONS) before a translation is accepted.
- **Formatting Settings**: Ensures that the translation preserves the source text's formatting (PRESERVE_SOURCE_FORMATTING).

This configuration file centralizes settings for the translation pipeline.

## [models.py](models.py)

The `models.py` file defines nine data models that structure and validate information related to the translation process, commentary, feedback, glossary entries, and translation quality verification. Each model is defined using **pydantic**. Thus, each model takes in a standard python dictionary and confirms that that dictionary includes the pre-determined keys and that their values is of the correct type.

### **Models**

1. **`CommentaryVerification`**: 
   - This model is used to verify the accuracy of a translation by comparing it against the key points from the commentary. It includes fields for tracking whether the translation aligns with the commentary, missing concepts, misinterpretations, and context accuracy.

2. **`GlossaryEntry`**:
   - Represents individual terms in a glossary, including the original Tibetan term, its English translation, contextual usage, entity category (e.g., person, place), and references to the commentary.

3. **`GlossaryExtraction`**:
   - Contains a list of `GlossaryEntry` objects, representing the complete glossary extracted from a translation.

4. **`Feedback`**:
   - This model captures feedback about the translation, including a grade (e.g., "bad", "okay", "good", "great") and detailed guidance for improving the translation based on commentary interpretation.

5. **`Translation_extractor`**:
   - Used to define an extracted translation, focusing on maintaining the exact format from the LLM response.

6. **`Translation`**:
   - Represents a translation that includes fields for determining whether the formatting matches the source text and storing detailed feedback for formatting.

7. **`KeyPoint`**:
   - Defines the core concept, required terminology, context, and philosophical implications of key points that need to be conveyed in a translation.

8. **`CommentaryPoints`**:
   - Contains a list of `KeyPoint` objects that represent the key points extracted from a commentary.

9. **`State`**:
   - A `TypedDict` representing the overall state of the translation process, including translations, commentary translations, feedback history, iteration count, glossary entries, and more.

These models help manage and structure the data involved in the translation, verification, and glossary extraction processes, ensuring consistency and enabling validation at different stages of the workflow.

## [prompts.py](prompts.py)

The `prompts.py` file contains a set of functions for generating prompts used throughout the translation and evaluation process. These prompts are used in generating translations, extracting key points from commentaries, verifying translations, and improving the overall translation quality based on feedback.

### Key Functions

#### Translation Prompts

- **get_translation_prompt**: generate a prompt for extracting translations from LLM responses

- **get_translation_improvement_prompt**: generate a prompt for improving a translation based on feedback

- **get_initial_translation_prompt**: generate a prompt for the initial translation of a Tibetan Buddhist text

#### Commentary and Key Points Extraction Prompts 

- **get_key_points_extraction_prompt**: generate a prompt to extract all key points that must be reflected in the translation 

- **get_commentary_translation_prompt**: generate a prompt to translate a commentary

#### Evaluation Prompts 
- **get_translation_evaluation_prompt**: generate a prompt for evaluating a translation against commentary and key points

- **get_verification_prompt**: generate a prompt to assess translation quality by comparing it to key points and commentary, while 

- **get_formatting_feedback_prompt**: generate a prompt to evaluate and improve translation formatting.

#### Glossary Extraction Prompts 
- **get_glossary_extraction_prompt**: generate a prompt to extract glossary terms from translations, focusing on Buddhist terminology and entities.

## [utils.py](utils.py)

The `utils.py` file contains utility functions that facilitate various tasks related to data handling, LLM prompting, and file management. The file initializes the LLM and provides three utility functions:

- `dict_to_text` converts a dictionary into a formatted text representation, useful for generating structured text output from dictionaries.

- `convert_state_to_jsonl`  saves a given state dictionary (of type `State`) to a file in JSONL format, appending it to the file.

- `get_json_data` loads data from a specified JSON file and returns it for further processing.

- `llm` instance is initialized using the `ChatAnthropic` class with the Claude 3.5 model and a specified maximum token limit. This instance is used for making API calls to the Anthropic LLM for translation and evaluation tasks.

## [workflow.py](workflow.py)

The `workflow.py` file defines a processing pipeline using the `StateGraph` from `langgraph`, structuring a series of steps in the translation process, as detailed below.

### **Flow Summary**

1. Start by translating commentaries (`commentary_translator_1`, `commentary_translator_2`, `commentary_translator_3`).
2. Aggregate the translations into a unified commentary (`aggregator`).
3. Generate the initial translation (`translation_generator`).
4. Evaluate the translation quality (`llm_call_evaluator`), and route it based on feedback (either proceed to formatting feedback or reattempt translation).
5. Evaluate and adjust formatting (`format_evaluator_feedback`), then either accept or adjust based on feedback.
6. If accepted, generate a glossary (`generate_glossary`), marking the process as complete.

### **Key Components**

1. **StateGraph Initialization**:
   - `StateGraph` is initialized with the `State` model, which tracks the current state of the workflow at any given point.

2. **Processing Nodes**:
   - **`commentary_translator_1`, `commentary_translator_2`, `commentary_translator_3`**: These nodes handle the translation of different commentaries in the Tibetan text.
   - **`aggregator`**: This node aggregates the translations from the different commentary translators.
   - **`translation_generator`**: Responsible for generating the translation based on aggregated commentary and source text.
   - **`llm_call_evaluator`**: Evaluates the generated translation, deciding whether it meets the criteria for acceptance.
   - **`format_evaluator_feedback`**: Analyzes the formatting of the translation and provides feedback.
   - **`generate_glossary`**: Extracts glossary terms from the final translation.
   - **`formater`**: Formats the translation based on the feedback received.

3. **Edges (Workflow Transitions)**:
   - The workflow defines the sequence of steps by adding edges between nodes. Each edge represents the transition from one step to the next.
   - **Conditional Edges**: The workflow includes conditional edges, where the outcome of a process (e.g., translation evaluation) decides which subsequent steps will be executed (e.g., if the translation is accepted, move to formatting feedback, if rejected, re-run the translation generation).

4. **Workflow Compilation**:
   - The final workflow is compiled using `optimizer_builder.compile()`, which integrates all the steps and conditional flows into a complete, executable process.