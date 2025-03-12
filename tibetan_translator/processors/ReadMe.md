# Processors

This folder consists of six files, excluding this ReadMe. These files are listed below along with links to the portion of this ReadMe that explains them. Each section header is also a link to the relevant code.

- **[\_\_init__.py](#initpy)**
- **[commentary.py](#commentarypy)**
- **[evaluation.py](#evaluationpy)**
- **[formatting.py](#formattingpy)**
- **[glossary.py](#glossarypy)**
- **[translation.py](#translationpy)**

These files provide a structured pipeline for translating Tibetan texts with commentary integration, evaluation, and refinement. It includes:

- **Commentary Processing ([commentary.py](#commentarypy))** – Extracts key points and translates thematic commentaries.
- **Translation Generation ([translation.py](#translationpy))** – Produces and iteratively improves translations.
- **Evaluation & Verification ([evaluation.py](#evaluationpy))** – Assesses translation accuracy against commentaries.
- **Formatting ([formatting.py](#formattingpy))** – Ensures structural fidelity to the source text.
- **Glossary Extraction ([glossary.py](#glossarypy))** – Identifies key terms for a structured glossary.

## [__init__.py](__init__.py)

This `__init__.py` file initializes the `tibetan_translator.processors` package by importing and exposing key translation-related modules. It allows users to access different processing functionalities—commentary handling, translation generation, evaluation, formatting, and glossary extraction—by importing from `tibetan_translator.processors` directly.

### **Expected Input & Output**  
This file itself does not take any direct inputs or produce direct outputs. Instead, it facilitates structured module imports, enabling users to access:  
- [`commentary`](#commentarypy): Handles commentary extraction and translation.   
- [`evaluation`](#evaluationpy): Evaluates translation quality against commentaries.  
- [`formatting`](#formattingpy): Ensures the translated text maintains proper structure.  
- [`glossary`](#glossarypy): Extracts key terms and generates a glossary.
- [`translation`](#translationpy): Manages translation generation and improvement. 

By importing `tibetan_translator.processors`, all these modules become accessible without needing individual imports.

## [commentary.py](commentary.py)

This module extracts and translates key points from multiple Tibetan commentaries, focusing on different interpretative approaches (expertise, philosophical, and traditional). It uses an LLM to process and translate each commentary, ensuring structured output. Additionally, it aggregates all commentaries, extracts key insights, and provides a summarized version for further analysis.  

### **Expected Input**  
- A `State` object containing:  
  - **`source`**: The original Tibetan text.  
  - **`sanskrit`**: Related Sanskrit text (if applicable).  
  - **`commentary1`**, **`commentary2`**, **`commentary3`**: Three different commentaries on the text.  

Example:  
```python
state = State(
    source="བདེ་གཤེགས་ཆོས་ཀྱི་སྐུ་མངའ་སྲས་བཅས་དང་། །ཕྱག་འོས་ཀུན་ལའང་གུས་པར་ཕྱག་འཚལ་ཏེ། །བདེ་གཤེགས་སྲས་ཀྱི་སྡོམ་ལ་འཇུག་པ་ནི། །ལུང་བཞིན་མདོར་བསྡུས་ནས་ནི་བརྗོད་པར་བྱ། །",
    sanskrit="सुगतान् ससुतान् सधर्मकायान् प्रणिपत्यादरतोऽखिलांश्च वन्द्यान्। सुगतात्मजसंवरावतारं कथयिष्यामि यथागमं समासात्॥१॥",
    commentary1="...",
    commentary2="...",
    commentary3="..."
)
```

### **Expected Output**  
- **Translated commentaries**:  
  - Each commentary is processed and translated separately.  
  - Outputs structured dictionaries like:  
    ```python
    {
        "commentary1": "Translated commentary text",
        "commentary1_translation": "Final extracted translation"
    }
    ```
- **Aggregated summary**:  
  - Combines all commentaries and extracts key insights.  
  - Outputs:  
    ```python
    {
        "combined_commentary": "Summarized version of all commentaries",
        "key_points": [KeyPoint(...), KeyPoint(...)]
    }
    ```

##  [evaluation.py](evaluation.py)

This module verifies translations of Tibetan texts by comparing them against key points from commentaries and evaluates the overall translation quality. It uses an LLM to validate the alignment of the translation with key commentary insights and to provide feedback and a grade. The module keeps track of the evaluation history and decides whether the translation is accepted or needs further improvement based on iteration count or formatting status.

### **Expected Input**  
- A `State` object containing:  
  - **`source`**: The original Tibetan text.  
  - **`translation`**: A list of translation versions, with the most recent used for evaluation.  
  - **`key_points`**: Extracted key points from the commentary.  
  - **`combined_commentary`**: The combined summary of commentaries.  
  - **`feedback_history`**: A list of feedback from previous evaluations.  
  - **`itteration`**: The number of feedback iterations the translation has gone through.  
  - **`formated`**: Boolean indicating whether the translation is properly formatted.

Example:  
```python
state = State(
    source="དཀར་པོ་ཆུང་བ།",
    translation=["small white"],
    key_points=["Key point 1", "Key point 2"],
    combined_commentary="...",
    feedback_history=[],
    itteration=1,
    formated=False
)
```

### **Expected Output**  
- **Verification**:  
  - Commentary verification is conducted by comparing the translation with key points.  
  - Outputs a `CommentaryVerification` object.
  
- **Evaluation results**:  
  - Provides feedback on the translation quality and updates the feedback history.  
  - Outputs a dictionary like:  
    ```python
    {
        "grade": "B",
        "feedback_history": ["Iteration 1 - Grade: B\nFeedback: Needs improvement on accuracy...\n"]
    }
    ```
  
- **Routing**:  
  - Based on the number of iterations or formatting, the translation is either accepted or rejected with feedback.
  - Outputs either `"Accepted"` or `"Rejected + Feedback"`.

## [formatting.py](formatting.py)

This module ensures that Tibetan translations maintain the correct structure and formatting relative to the source text. It uses an LLM to refine the translation by providing feedback on formatting inconsistencies and iteratively improving the structure. The evaluation function determines whether the formatting matches expectations and either accepts the translation or adds feedback for further refinement.

### **Expected Input**  
- A `State` object containing:  
  - **`source`**: The original Tibetan text.  
  - **`translation`**: A list of translation versions, with the most recent used for formatting evaluation.  
  - **`format_feedback_history`**: A list of previous feedback entries regarding formatting.  
  - **`itteration`**: The number of formatting correction attempts.

Example:  
```python
state = State(
    source="དཀར་པོ་ཆུང་བ།",
    translation=["small white"],
    format_feedback_history=[],
    itteration=1
)
```

### **Expected Output**  
- **Formatted Translation**:  
  - The LLM refines the translation to match the source structure.  
  - Outputs a dictionary with an updated translation list:  
    ```python
    {
        "translation": ["small white", "properly formatted translation"]
    }
    ```

- **Formatting Evaluation**:  
  - Determines if the translation is correctly formatted.  
  - If formatting is correct:  
    ```python
    {"formated": True, "translation": ["properly formatted translation"]}
    ```
  - If formatting needs improvement, feedback is added, and the iteration count is updated:  
    ```python
    {
        "formated": False,
        "translation": ["small white"],
        "format_feedback_history": ["Formatting issue: Sentence structure mismatch"],
        "itteration": 2
    }
    ```

## [glossary.py](glossary.py)

This module extracts technical terms from Tibetan translations and saves them as a structured glossary. It uses an LLM to identify key terms from the source text, commentary, and latest translation, returning structured `GlossaryEntry` objects. The extracted glossary is then saved to a CSV file, appending new entries if the file already exists.  

The process is automated through the `generate_glossary()` function, which orchestrates extraction and file generation. This ensures that technical terms and their contextual information are systematically stored for reference or further processing within the larger project.

### **Expected Input**  
- A `State` object containing:  
  - **`source`**: The original Tibetan text.  
  - **`combined_commentary`**: Relevant commentary on the text.  
  - **`translation`**: A list of translation versions, with the most recent one used.  

Example:  
```python
state = State(
    source="དཀར་པོ་ཆུང་བ།",
    combined_commentary="...",
    translation=["small white"]
)
```

### **Expect Output**  
- A **list of extracted glossary entries**, each containing:  
  - `tibetan_term`: The term in Tibetan.  
  - `translation`: The corresponding translation.  
  - `category`: Part of speech or classification.  
  - `context`: Usage context.  
  - `commentary_reference`: Source or reference for the term.  
  - `entity_category`: General classification of the term.  

Example Output:  
```python
[
    GlossaryEntry(
        tibetan_term="དཀར་པོ་",
        translation="white",
        category="adjective",
        context="Used to describe objects",
        commentary_reference="Classical Tibetan Dictionary",
        entity_category="descriptive term"
    )
]
```
Additionally, the extracted glossary is saved or updated in `translation_glossary.csv` by default.

## [translation.py](translation.py)

This module generates, iteratively improves, and evaluates Tibetan translations using an LLM. It starts with an initial translation and refines it based on feedback from previous iterations. If the translation meets quality standards or reaches a maximum iteration threshold, it is accepted; otherwise, further improvements are requested.

### **Expected Input**  
- A `State` object containing:  
  - **`sanskrit`**: The Sanskrit equivalent of the Tibetan text, if available.  
  - **`source`**: The original Tibetan text.  
  - **`translation`**: A list of translation versions, with the most recent used for refinement.  
  - **`combined_commentary`**: A compiled summary of multiple commentaries.  
  - **`key_points`**: Extracted key points from the commentary.  
  - **`feedback_history`**: A list of previous feedback entries on translation quality.  
  - **`itteration`**: The number of translation improvement attempts.  
  - **`grade`**: A quality rating for the latest translation.

Example:  
```python
state = State(
    sanskrit="श्वेत",
    source="དཀར་པོ་ཆུང་བ།",
    translation=["small white"],
    combined_commentary="...",
    key_points=["Key point 1", "Key point 2"],
    feedback_history=[],
    itteration=1,
    grade="acceptable"
)
```

### **Expected Output**  
- **Translation Generation & Refinement**:  
  - If no previous feedback exists, generates an initial translation.  
  - If feedback exists, improves the translation accordingly.  
  - Example output after improvement:  
    ```python
    {
        "translation": ["small white", "refined translation"],
        "itteration": 2
    }
    ```
  
- **Translation Routing**:  
  - Determines if the translation is accepted or needs further revision.  
  - If the translation quality is rated `"great"` or the iteration count reaches 4, it is accepted.  
  - Otherwise, it returns `"Rejected + Feedback"`.  
  - Example outputs:  
    ```python
    "Accepted"
    ```
    or  
    ```python
    "Rejected + Feedback"
    ```