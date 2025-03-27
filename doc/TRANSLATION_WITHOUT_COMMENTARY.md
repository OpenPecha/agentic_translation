# Translation Without Commentary

This document explains how the translation system works when commentaries are not present, detailing the workflow and processes involved.

## Overview

When commentaries are not available, the system switches to a "source-focused" translation mode. This approach relies on direct linguistic analysis of the Tibetan source text rather than interpretation through commentaries.

## Workflow Steps

1. **Commentary Detection**
   - The system checks for commentary presence using:
     ```python
     is_source_focused = not state.get('commentary1') and not state.get('commentary2') and not state.get('commentary3')
     ```
   - When no commentaries are found, the system automatically switches to source-focused mode

2. **Source Analysis Generation**
   - Instead of using commentaries, the system generates linguistic analysis of the source text
   - The `create_source_analysis()` function is called to produce detailed linguistic information
   - This analysis examines grammar, terminology, structure, and cultural context

3. **Enhanced Translation Prompting**
   - Uses a specialized prompt through `get_enhanced_translation_prompt()`
   - The prompt includes:
     - The Sanskrit parallel text (if available)
     - The Tibetan source text
     - The generated source analysis
     - Target language specification

4. **Translation Generation**
   - The LLM generates a contextually appropriate translation focusing on:
     - Accuracy of terminology
     - Fluency in the target language
     - Preservation of original meaning
     - Cultural and philosophical context

5. **Plain Translation**
   - In parallel, a plain/literal translation is also generated for accessibility
   - This provides a more direct rendering of the source text

6. **Translation Extraction**
   - The structured output is extracted using the `Translation_extractor` model
   - Ensures consistent output format

7. **Quality Evaluation**
   - Translation quality assessment checks for:
     - Completeness
     - Accuracy of terminology
     - Fluency and clarity
     - Formatting correctness

8. **Glossary Generation**
   - Final step extracts key terms and their translations
   - Helps maintain consistency in terminology

## LangGraph Workflow

The workflow is managed through LangGraph with these key components:

```
START
  ↓
commentary_translator_1, commentary_translator_2, commentary_translator_3 (parallel)
  ↓
aggregator (creates source analysis when no commentaries exist)
  ↓
translation_generator (uses enhanced translation prompt)
  ↓
llm_call_evaluator
  ↓
[conditional] → translation_generator (if rejected)
  ↓
generate_glossary
  ↓
END
```

## Usage Examples

### Basic API Usage

```python
from tibetan_translator import optimizer_workflow

# Initialize the workflow with empty commentary fields
state = optimizer_workflow.invoke(
    {
        "source": "ཇི་ལྟར་མཐོང་ཐོས་ཤེས་པ་དག །\nའདིར་ནི་དགག་པར་བྱ་མིན་ཏེ། །\nའདིར་ནི་སྡུག་བསྔལ་རྒྱུར་གྱུར་པ། །\nབདེན་པར་རྟོག་པ་བཟློག་བྱ་ཡིན། །",
        "sanskrit": "यथा दृष्टं श्रुतं ज्ञातं नैवेह प्रतिषिध्यते। सत्यतः कल्पना त्वत्र दुःखहेतुर्निवार्यते॥२६",
        "feedback_history": [],
        "format_feedback_history": [],
        "itteration": 0,
        "format_iteration": 0,
        "formated": False,
        "glossary": [],
        "commentary1": "",  # Empty commentary
        "commentary2": "",  # Empty commentary
        "commentary3": "",  # Empty commentary
        "language": "English",
    },
    debug=True,
)
```

### Command Line Usage

For simpler translations without the full LangGraph workflow:

```bash
# Simple translation to English
python simple_translate.py input.json

# Simple translation to Chinese
python simple_translate.py input.json --target-lang Chinese

# Batch processing multiple files
python simple_translate.py file1.json file2.json --target-lang Hindi
```

## Input & Output Format

### Input JSON Format

```json
{
  "root": "ཇི་ལྟར་མཐོང་ཐོས་ཤེས་པ་དག །\nའདིར་ནི་དགག་པར་བྱ་མིན་ཏེ།",
  "commentary": "",  // Empty commentary triggers source-focused mode
  "sanskrit": "यथा दृष्टं श्रुतं ज्ञातं नैवेह प्रतिषिध्यते।"
}
```

### Output JSON Format

```json
{
  "root": "ཇི་ལྟར་མཐོང་ཐོས་ཤེས་པ་དག །\nའདིར་ནི་དགག་པར་བྱ་མིན་ཏེ།",
  "commentary": "",
  "sanskrit": "यथा दृष्टं श्रुतं ज्ञातं नैवेह प्रतिषिध्यते।",
  "translation": "That which is seen, heard, and known\nIs not to be negated here.",
  "plain_translation": "As for what is seen, heard, and known,\nHere it is not to be negated.",
  "glossary": [
    {"term": "མཐོང་", "translation": "seen"},
    {"term": "ཐོས་", "translation": "heard"},
    {"term": "ཤེས་པ་", "translation": "known"}
  ]
}
```

## Differences from Commentary-Based Translation

1. **Focus on Source Text**
   - Direct analysis of the Tibetan source rather than relying on commentarial interpretation
   - More attention to grammatical and structural elements

2. **Linguistic Analysis**
   - Generates comprehensive linguistic analysis of the source text
   - Examines grammatical structures, terminology, and cultural context

3. **Translation Approach**
   - More literal/direct translation when appropriate
   - Less interpretive than commentary-based translation
   - Maintains faithfulness to the original source

4. **Output**
   - Final output structure remains the same as commentary-based translation
   - Includes both standard and plain translations
   - Includes glossary of key terms

## Alternative Implementation

The system also supports simpler alternative implementations:

1. **simple_translate.py**: A streamlined approach using Google's Gemini model
   - Direct translation without the LangGraph workflow
   - Supports multiple languages and batch processing
   - Lower computational requirements

2. **zero_shot_translator.py**: Batch processing implementation
   - Parallel processing of multiple texts
   - No intermediate steps or feedback loops
   - Suitable for large volume, lower complexity translations