# Quickstart

## Installation

Begin by cloning this repository to your local machine like so:

```
git clone https://github.com/OpenPecha/agentic_translation
```

Navigate to the newly installed folder.

Ensure you have Python installed (>=3.8), then install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The CLI tool for the Tibetan Translator can be run like so:

```bash
python cli.py --input input_data.json --output output_results.jsonl --batch_size 8 --preprocess
```

This will:
- Read data from `input_data.json`. (See below for example input.)
- Process the data in batches of 8.
- Preprocess the data before running the translation workflow.
- Save the results in `output_results.jsonl`. (See below for example output.)

## Example Input and Output

### **Input JSON Structure**
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


### Output

The output of the translation process will be a **JSONL (JSON Lines)** format file, where each line is a JSON object representing the state of a translation task after processing. The structure of the output will be similar to the input, but with additional data generated as part of the workflow, including translations, commentary analysis, formatting feedback, and glossary entries.

#### **Output JSONL Structure**
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

This output reflects a fully processed translation task, including commentary translations, key points, glossary entries, and formatted text.