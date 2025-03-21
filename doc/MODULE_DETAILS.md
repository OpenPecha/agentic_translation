# Tibetan Translator: Detailed Module Documentation

This document provides in-depth technical details about each component of the Tibetan Buddhist Translation System, including key functions, data models, prompt designs, and implementation details.

## Table of Contents

1. [Data Models](#data-models)
2. [Commentary Processing](#commentary-processing)
3. [Translation Generation](#translation-generation)
4. [Evaluation System](#evaluation-system)
5. [Formatting System](#formatting-system)
6. [Glossary Generation](#glossary-generation)
7. [Workflow Orchestration](#workflow-orchestration)
8. [Utility Functions](#utility-functions)
9. [Batch Processing](#batch-processing)

## Data Models

The system uses Pydantic models for structured data handling and validation:

### Core State Model

```python
class State(TypedDict):
    translation: List[str]  # List of translations (for tracking iterations)
    commentary1_translation: str  # Translated commentary 1
    commentary2_translation: str  # Translated commentary 2
    commentary3_translation: str  # Translated commentary 3
    source: str  # Original Tibetan text
    sanskrit: str  # Sanskrit equivalent
    language: str  # Target language
    feedback_history: List[str]  # History of translation feedback
    format_feedback_history: List[str]  # History of formatting feedback
    commentary1: str  # Original commentary 1
    commentary2: str  # Original commentary 2
    commentary3: str  # Original commentary 3
    combined_commentary: str  # Integrated commentary
    key_points: List[KeyPoint]  # Key points extracted from commentaries
    plaintext_translation: str  # Simplified translation
    itteration: int  # Current translation iteration counter
    format_iteration: int  # Current formatting iteration counter
    formated: bool  # Whether formatting is complete
    glossary: List[GlossaryEntry]  # Extracted glossary entries
```

### Evaluation Models

```python
class CommentaryVerification(BaseModel):
    matches_commentary: bool
    missing_concepts: str
    misinterpretations: str
    context_accuracy: str

class Feedback(BaseModel):
    grade: Literal["bad", "okay", "good", "great"]
    feedback: str
    format_matched: bool
    format_issues: str
```

### Translation Models

```python
class Translation_extractor(BaseModel):
    extracted_translation: str

class Translation(BaseModel):
    format_matched: bool
    extracted_translation: str
    feedback_format: str
```

### Glossary Models

```python
class GlossaryEntry(BaseModel):
    tibetan_term: str
    translation: str
    context: str
    entity_category: str
    commentary_reference: str
    category: str

class GlossaryExtraction(BaseModel):
    entries: List[GlossaryEntry]
```

### Commentary Models

```python
class KeyPoint(BaseModel):
    concept: str
    terminology: List[str]
    context: str
    implications: List[str]

class CommentaryPoints(BaseModel):
    points: List[KeyPoint]
```

## Commentary Processing

### Commentary Translation Process

The system translates three types of commentaries using specialized processors:

1. `commentary_translator_1`: Translates with expertise focus
2. `commentary_translator_2`: Translates with philosophical focus
3. `commentary_translator_3`: Translates with traditional interpretation focus

Each translator follows the same pattern:

```python
def commentary_translator_X(state: State):
    # Skip if commentary is empty
    if not state['commentaryX']:
        return {"commentaryX": None, "commentaryX_translation": None}
    
    # Create translation prompt with target language
    prompt = get_commentary_translation_prompt(
        state['sanskrit'], 
        state['source'], 
        state['commentaryX'],
        language=state.get('language', 'English')
    )
    
    # Generate translation
    commentary_X = llm.invoke(prompt)
    
    # Extract structured translation
    commentary_X_ = llm.with_structured_output(Translation_extractor).invoke(
        get_translation_prompt(state['commentaryX'], commentary_X.content)
    )
    
    # Return both original response and extracted translation
    return {
        "commentaryX": commentary_X.content, 
        "commentaryX_translation": commentary_X_.extracted_translation
    }
```

### Commentary Aggregation

The aggregator combines all available commentaries into a coherent explanation:

```python
def aggregator(state: State):
    # Check if any commentaries exist
    has_commentary1 = state.get('commentary1_translation') not in [None, "", "None"]
    has_commentary2 = state.get('commentary2_translation') not in [None, "", "None"]
    has_commentary3 = state.get('commentary3_translation') not in [None, "", "None"]
    
    has_any_commentaries = has_commentary1 or has_commentary2 or has_commentary3
    
    # Create the combined commentaries string if any exist
    combined = ""
    if has_any_commentaries:
        if has_commentary1:
            combined += f"Commentary 1:\n{state['commentary1_translation']}\n\n"
        if has_commentary2:
            combined += f"Commentary 2:\n{state['commentary2_translation']}\n\n"
        if has_commentary3:
            combined += f"Commentary 3:\n{state['commentary3_translation']}\n\n"
    
    # Get target language
    language = state.get('language', 'English')
    
    # Create prompt based on commentary availability
    prompt_messages = get_combined_commentary_prompt(
        source_text=state['source'], 
        commentaries=combined,
        has_commentaries=has_any_commentaries,
        language=language
    )
    
    # Use thinking LLM for analysis
    response = llm_thinking.invoke(prompt_messages)
    
    # Extract content from response
    commentary_content = extract_content_from_thinking(response)
    
    # Return combined commentary
    return {"combined_commentary": commentary_content}
```

### Commentary Prompt Design

```python
def get_combined_commentary_prompt(source_text, commentaries, has_commentaries=True, language="English"):
    """Generate a prompt for creating combined commentary, with fallback for cases with no commentaries."""
    # If there are no commentaries, use zero-shot mode instead
    if not has_commentaries:
        return get_zero_shot_commentary_prompt(source_text, language)
    
    system_message = SystemMessage(content=f"""You are an expert in Tibetan Buddhist philosophy tasked with creating a comprehensive, integrated commentary on Tibetan Buddhist texts. Your task is to:

1. Analyze multiple commentaries on the same text and integrate them into a single cohesive explanation
2. Preserve all key philosophical points from each commentary
3. Explain each line of the source text in detail, including its doctrinal significance
4. Connect the commentaries in a way that builds a clearer understanding of the text
5. Ensure all technical Buddhist terminology is properly explained

Your combined commentary should be thorough, scholarly, and provide a complete analysis of the text.
IMPORTANT: Your commentary MUST be written in {language}.""")
    
    # Add few-shot examples and actual request
    # ...
```

## Translation Generation

### Translation Process

The translation generator has two primary modes:

1. Initial translation generation
2. Iterative improvement based on feedback

```python
def translation_generator(state: State):
    """Generate improved translation based on commentary and feedback."""
    current_iteration = state.get("itteration", 0)

    if state.get("feedback_history"):
        # Iterative improvement mode
        latest_feedback = state["feedback_history"][-1]
        prompt = get_translation_improvement_prompt(
            state['sanskrit'], state['source'], state['combined_commentary'], 
            latest_feedback, state['translation'][-1],
            language=state.get('language', 'English')
        )
        msg = llm.invoke(prompt)
        translation = extract_structured_translation(state['source'], msg.content)
        return {
            "translation": state["translation"] + [translation],
            "itteration": current_iteration + 1
        }
    else:
        # Initial translation mode
        # Generate main translation
        prompt = get_initial_translation_prompt(
            state['sanskrit'], state['source'], state['combined_commentary'], 
            language=state.get('language', 'English')
        )
        thinking_response = llm_thinking.invoke(prompt)
        translation_content = extract_text_from_thinking(thinking_response)
        
        # Generate plain language translation
        target_language = state.get('language', 'English')
        plain_translation_prompt = get_plain_translation_prompt(state['source'], language=target_language)
        plain_translation_response = llm.invoke(plain_translation_prompt)
        plain_content = extract_content(plain_translation_response)
        
        # Extract structured translations
        translation = extract_structured_translation(state['source'], translation_content)
        plain_translation = extract_structured_translation(state['source'], plain_content)
        
        # Create feedback entry
        feedback_entry = create_feedback_entry(current_iteration, translation_content, thinking_response)
        
        return {
            "translation": [translation],
            "plaintext_translation": plain_translation,
            "feedback_history": [feedback_entry],
            "iteration": 1
        }
```

### Translation Prompt Design

The initial translation prompt emphasizes creating natural, fluent translations in the target language:

```python
def get_initial_translation_prompt(sanskrit, source, combined_commentary, language="English"):
    """Generate a prompt for the initial translation of a Tibetan Buddhist text."""
    return f"""
Translate this Tibetan Buddhist text into natural, fluent {language}:

Sanskrit text:
{sanskrit}

Source Text:
{source}

Context (Including Analysis):
{combined_commentary}

LANGUAGE-SPECIFIC REQUIREMENTS FOR {language.upper()}:
- Your translation MUST be in fluent, natural {language} as spoken by native speakers
- Use appropriate {language} grammar, syntax, and idiomatic expressions
- Maintain proper {language} sentence structure and flow
- Use culturally-appropriate and accurate terminology in {language}
- Avoid awkward phrasing, word-for-word translations, or unnatural constructions
- Technical Buddhist terms should be translated using established {language} conventions when available

Translation guidance:
- Freely restructure sentences to achieve natural {language} expression
- Prioritize accuracy of Buddhist concepts and doctrinal meaning
- Preserve all content and implied meanings from the original
- Choose the best way to convey the intended meaning in natural {language}
- Refer to the Sanskrit text as well as the Tibetan text, as the Tibetan text is translated from the Sanskrit text
- The translation should be detailed and should preserve verse format if the original is in verse
- The translation is not an explanation of the text but a direct translation expressed naturally in {language}
- Use the analysis section in the context for deeper understanding of Buddhist concepts

YOUR GOAL: Create a translation that sounds as if it were originally written in {language} by a native speaker with expertise in Buddhism.

Generate the translation in a clear and structured format matching the source text structure."""
```

### Plain Translation Design

The plain translation feature creates an accessible version with simpler language:

```python
def get_plain_translation_prompt(source_text, language="English"):
    """Generate a few-shot prompt for plain language translation using a multi-turn conversation format."""
    system_message = SystemMessage(content=f"""You are an expert translator of Tibetan Buddhist texts into clear, accessible modern {language}. Your task is to:

1. Create a plain, accessible translation that preserves the meaning but uses simple, straightforward {language}
2. Focus on clarity and readability for modern readers without specialized Buddhist knowledge
3. Make the translation direct and concise while maintaining all key content
4. Use natural, flowing language that would be understood by educated non-specialists

LANGUAGE-SPECIFIC REQUIREMENTS FOR {language.upper()}:
- Your translation MUST be in fluent, natural {language} as spoken by native speakers
- Use appropriate {language} grammar, syntax, and idiomatic expressions
- Maintain proper {language} sentence structure and flow
- Choose words and phrases that sound natural in {language}
- Avoid awkward phrasing, word-for-word translations, or unnatural constructions

Your translation should be accurate but prioritize clarity, naturalness, and accessibility over technical precision.
IMPORTANT: Your translation MUST be in {language} and must sound natural to native {language} speakers.""")
    
    # Add few-shot examples using multi-turn conversation format
    # ...
```

## Evaluation System

### Unified Evaluation Process

The evaluation system combines content and formatting assessment:

```python
def llm_call_evaluator(state: State):
    """Evaluate translation quality AND formatting with comprehensive verification."""
    previous_feedback = "\n".join(state["feedback_history"]) if state["feedback_history"] else "No prior feedback."
    
    language = state.get('language', 'English')
    
    # Perform structured verification
    verification = verify_against_commentary(
        state['translation'][-1], 
        state['combined_commentary'],
        language=language
    )
        
    # Generate comprehensive evaluation prompt
    prompt = get_translation_evaluation_prompt(
        state['source'], state['translation'][-1], state['combined_commentary'], 
        verification, previous_feedback, 
        language=language
    )
    
    # Get structured evaluation
    evaluation = llm.with_structured_output(Feedback).invoke(prompt)
    
    # Create comprehensive feedback entry
    feedback_entry = f"Iteration {state['itteration']} - Grade: {evaluation.grade}\n"
    feedback_entry += f"Format Matched: {evaluation.format_matched}\n"
    
    if evaluation.format_issues:
        feedback_entry += f"Format Issues: {evaluation.format_issues}\n"
    
    feedback_entry += f"Content Feedback: {evaluation.feedback}\n"
    
    return {
        "grade": evaluation.grade,
        "formated": evaluation.format_matched,
        "feedback_history": state["feedback_history"] + [feedback_entry],
        "format_feedback_history": state.get("format_feedback_history", []) + 
                                  ([evaluation.format_issues] if evaluation.format_issues else [])
    }
```

### Verification Function

```python
def verify_against_commentary(translation: str, combined_commentary: str, language: str = "English") -> CommentaryVerification:
    """Verify translation against commentary."""
    verification_prompt = get_verification_prompt(translation, combined_commentary, language=language)
    verification = llm.with_structured_output(CommentaryVerification).invoke(verification_prompt)
    return verification
```

### Routing Logic

```python
def route_translation(state: State):
    """Route based on both translation quality and formatting."""
    # Only proceed if both content is good AND formatting is correct
    if state["grade"] == "great" and state["formated"]:
        return "Accepted"
    # Max iterations reached but still try to continue with best effort
    elif state["itteration"] >= MAX_TRANSLATION_ITERATIONS:
        return "Accepted"
    else:
        return "Rejected + Feedback"
```

### Evaluation Prompt Design

```python
def get_translation_evaluation_prompt(source, translation, combined_commentary, verification, previous_feedback, language="English"):
    """Generate a prompt for evaluating a translation against commentary with language-specific feedback."""
    # Count the number of lines in the source
    source_lines = len([line for line in source.split('\n') if line.strip()])
    
    return f"""Evaluate this translation comprehensively for content accuracy, structural formatting, AND linguistic fluency in {language}:

Source Text: {source}
Target Language: {language}
Translation: {translation}

Commentary (Including Analysis):
{combined_commentary}

Previous Feedback:
{previous_feedback}

Verification Results:
{verification}

CRITICAL STRUCTURAL REQUIREMENTS:
- Source has approximately {source_lines} lines/segments - translation MUST have similar structure
- If source is in verse form, translation MUST be in verse form
- Paragraph breaks and line breaks MUST match the source text structure
- Sentence boundaries should respect the source text

LANGUAGE-SPECIFIC REQUIREMENTS FOR {language.upper()}:
- Translation must sound natural and fluent to native {language} speakers
- Use appropriate {language} grammar, syntax, and idiomatic expressions
- Maintain proper {language} sentence structure and flow
- Use culturally-appropriate and accurate terminology in {language}
- Avoid awkward phrasing, word-for-word translations, or unnatural constructions
- Technical Buddhist terms should be translated using established {language} conventions when available

CONTENT EVALUATION CRITERIA:
1. Commentary alignment
2. Technical terminology accuracy
3. Philosophical precision
4. Contextual preservation
5. Use of insights from analysis section in the commentary
6. Linguistic coherence and natural flow in {language}

Grade criteria:
- "great": Perfect alignment with commentary, correct formatting, AND natural, fluent {language}
- "good": Minor deviations in content OR minor formatting/linguistic issues
- "okay": Several misalignments, structural issues, or awkward language
- "bad": Major divergence in content, structure, or poor {language} fluency

For your response, provide:
1. A grade (great/good/okay/bad)
2. Whether the format matches the source structure (true/false)
3. Specific formatting issues (if any)
4. {language}-specific linguistic feedback (focus on naturalness, fluency, and accuracy)
5. Detailed content feedback for improvements

IMPORTANT: Your evaluation MUST be in {language}. Provide all feedback in {language} with specific suggestions for how to improve the translation's fluency and naturalness in {language}.

Formatting issues, incorrect structure, and unnatural language are ALL CRITICAL problems that must be fixed for a translation to be acceptable."""
```

## Glossary Generation

### Glossary Extraction Process

```python
def extract_glossary(state: State) -> List[GlossaryEntry]:
    """Extract technical terms and their translations into a glossary."""
    glossary_prompt = get_glossary_extraction_prompt(
        state['source'], state['combined_commentary'], state['translation'][-1],
        language=state.get('language', 'English')
    )
    extractor = llm.with_structured_output(GlossaryExtraction)
    result = extractor.invoke(glossary_prompt)
    return result.entries
```

### Glossary CSV Generation

```python
def generate_glossary_csv(entries: List[GlossaryEntry], filename: str = "translation_glossary.csv"):
    """Generate or append to a CSV file from glossary entries."""
    new_df = pd.DataFrame([entry.dict() for entry in entries])
    column_order = ['tibetan_term', 'translation', 'category', 'context', 'commentary_reference', 'entity_category']
    new_df = new_df[column_order]
    
    try:
        existing_df = pd.read_csv(filename, encoding='utf-8')
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_csv(filename, index=False, encoding='utf-8')
    except FileNotFoundError:
        new_df.to_csv(filename, index=False, encoding='utf-8')
    
    return filename
```

### Glossary Prompt Design

```python
def get_glossary_extraction_prompt(source, combined_commentary, final_translation, language="English"):
    """Generate a prompt for extracting glossary terms from a translation."""
    return f"""
Extract a comprehensive glossary from the final {language} translation only:

Source Text:
{source}

Combined Commentary:
{combined_commentary}

Final Translation:
{final_translation}

For each technical term, provide:
1. Original Tibetan term in the Source Text
2. Exact {language} translation term used
3. Usage context (IMPORTANT: This MUST be written in {language})
4. Commentary reference (IMPORTANT: This MUST be written in {language})
5. Term category (e.g., philosophical, technical, ritual, doctrinal) (In {language})
6. Entity category (e.g., person, place, etc.), if not entity then leave it blank

Focus on:
- Buddhist terms
- Important Entities (names of people, places, etc.)
- Specialized vocabulary in Buddhist Texts
- Do not use any terms that are not in the Source text
- Do not use any terms from the Commentary unless it overlaps with the Source text

CRITICAL INSTRUCTIONS:
- ALL descriptions, context, explanations, and categorical information MUST be in {language}
- DO NOT provide any content in English unless the target language is English
- The only field that should not be in {language} is the original Tibetan term

Format the extracted glossary in a structured data format."""
```

## Workflow Orchestration

### LangGraph Configuration

```python
# Initialize the workflow graph
optimizer_builder = StateGraph(State)

# Add processing nodes
optimizer_builder.add_node("commentary_translator_1", commentary_translator_1)
optimizer_builder.add_node("commentary_translator_2", commentary_translator_2)
optimizer_builder.add_node("commentary_translator_3", commentary_translator_3)
optimizer_builder.add_node("aggregator", aggregator)
optimizer_builder.add_node("translation_generator", translation_generator)
optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)
optimizer_builder.add_node("generate_glossary", generate_glossary)

# Define workflow edges
optimizer_builder.add_edge(START, "commentary_translator_1")
optimizer_builder.add_edge(START, "commentary_translator_2")
optimizer_builder.add_edge(START, "commentary_translator_3")
optimizer_builder.add_edge("commentary_translator_1", "aggregator")
optimizer_builder.add_edge("commentary_translator_2", "aggregator")
optimizer_builder.add_edge("commentary_translator_3", "aggregator")
optimizer_builder.add_edge("aggregator", "translation_generator")
optimizer_builder.add_edge("translation_generator", "llm_call_evaluator")

optimizer_builder.add_conditional_edges(
    "llm_call_evaluator",
    route_translation,
    {
        "Accepted": "generate_glossary",
        "Rejected + Feedback": "translation_generator"
    }
)

optimizer_builder.add_edge("generate_glossary", END)

# Compile the workflow
optimizer_workflow = optimizer_builder.compile()
```

## Utility Functions

### Few-shot Prompt Generation

```python
def get_translation_extraction_prompt(source_text, llm_response):
    """Generate a few-shot prompt for translation extraction."""
    system_message = SystemMessage(content="""You are an expert assistant specializing in extracting translations from text. Your task is to:

1. Identify the actual translation portion of the text
2. Extract ONLY the translation, not any translator's notes, explanations, or formatting instructions
3. Preserve the exact formatting of the translation including line breaks
4. Remove any metadata, headers, or annotations that are not part of the translation itself

DO NOT include any explanatory text or commentary in your extraction. Return ONLY the translation text.""")
    
    # Create few-shot examples as a conversation
    messages = [system_message]
    
    # Add few-shot examples
    for example in translation_extraction_examples:
        # Add user message with request
        messages.append(HumanMessage(content=f"""Extract the translation from the following text:

SOURCE TEXT:
{example['source']}

LLM RESPONSE:
This is a translation of the Tibetan text above. The Tibetan says: {example['source']}

Translation:
{example['translation']}

Note: This translation preserves the meaning while making it accessible in natural English. The term "Bhagavan" refers to the Buddha...
"""))
        
        # Add assistant's correct response as an AI message
        messages.append({"type": "ai", "content": example['translation']})
    
    # Add the actual request
    messages.append(HumanMessage(content=f"""Extract the translation from the following text:

SOURCE TEXT:
{source_text}

LLM RESPONSE:
{llm_response}

Return ONLY the translation portion, no explanatory text or metadata."""))
    
    return messages
```

### Thinking Response Handling

```python
def extract_text_from_thinking(response):
    """Extract text content from a thinking response."""
    if isinstance(response, list):
        # Just extract the text portion (second dictionary with text key)
        for chunk in response:
            if isinstance(chunk, dict) and chunk.get('type') == 'text':
                return chunk.get('text', '')
    elif hasattr(response, 'content'):
        if isinstance(response.content, list) and len(response.content) > 1:
            # Extract text from the second element (typical thinking response structure)
            return response.content[1].get('text', '')
        return response.content
    return str(response)
```

### JSONL Handling

```python
def convert_state_to_jsonl(state_dict: dict, file_path: str):
    """Save the state dictionary in JSONL format, handling custom objects."""
    with open(file_path, 'a', encoding='utf-8') as f:  # Append mode for JSONL
        json.dump(state_dict, f, cls=CustomEncoder, ensure_ascii=False)
        f.write("\n")

class CustomEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
```

## Batch Processing

### Robust Processing Logic

```python
def run_robust_batch_processing(
    data: List[Dict[str, Any]], 
    batch_size: int = 2,
    max_retries: int = 3,
    retry_delay: int = 5,
    run_name: str = "batch_run",
    language: str = "English"
) -> Tuple[List[State], List[Dict[str, Any]]]:
    """Run translation workflow with robust error handling and fallback strategies."""
    # Preprocess data
    examples = preprocess_data(data, language)
    
    # Create batches
    batches = create_batches(examples, batch_size)
    
    all_results = []
    all_failures = []
    
    # Process batches with retry logic
    for batch_idx, batch in enumerate(batches):
        batch_success = False
        batch_retries = 0
        
        # Try batch processing with retries
        while not batch_success and batch_retries < max_retries:
            try:
                results = process_batch(batch_idx, batch, batch_retries, max_retries)
                save_results(results, run_name)
                all_results.extend(results)
                batch_success = True
            except Exception as e:
                handle_batch_error(e, batch_idx, batch_retries, max_retries, retry_delay)
                batch_retries += 1
        
        # Fall back to individual processing if batch fails
        if not batch_success:
            individual_results, individual_failures = process_items_individually(
                batch, max_retries, retry_delay, run_name
            )
            all_results.extend(individual_results)
            all_failures.extend(individual_failures)
    
    return all_results, all_failures
```

### Individual Item Processing

```python
def process_items_individually(batch, max_retries, retry_delay, run_name):
    """Process items individually when batch processing fails."""
    individual_results = []
    individual_failures = []
    
    for item_idx, item in enumerate(batch):
        item_success = False
        item_retries = 0
        
        # Try individual processing with retries
        while not item_success and item_retries < max_retries:
            try:
                result = process_single_item(item_idx, item, item_retries, max_retries)
                save_single_result(result, run_name)
                individual_results.append(result)
                item_success = True
            except Exception as e:
                handle_item_error(e, item_idx, item_retries, max_retries, retry_delay)
                item_retries += 1
                
        # Handle persistent failures
        if not item_success:
            handle_persistent_failure(item, run_name)
            individual_failures.append(item)
    
    return individual_results, individual_failures
```

### Standalone Glossary Tool

```python
def compile_glossary_from_jsonl(input_files: List[str], output_file: str) -> None:
    """Compile a glossary from one or more JSONL files containing translation states."""
    all_entries = []
    
    # Process each input file
    for input_file in input_files:
        states = load_jsonl(input_file)
        
        # Extract glossary entries from each state
        for state in states:
            entries = extract_glossary_entries(state)
            all_entries.extend(entries)
    
    # Deduplicate entries
    unique_entries = deduplicate_entries(all_entries)
    
    # Create CSV
    create_glossary_csv(unique_entries, output_file)
```