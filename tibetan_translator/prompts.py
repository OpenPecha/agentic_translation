def get_translation_prompt(source, example):
    return f"""
    Extract the translation with exact format from the response:
     Source text:
     {source}

     LLM translation Response:
     {example}
    """

def get_key_points_extraction_prompt(commentary):
    return f"""Analyze this commentary and extract all key points that must be reflected in the translation:
    Sanskrit text:

{commentary}

For each key point, provide:
1. The core concept or interpretation
2. Required terminology that must be used
3. Essential context that must be preserved
4. Philosophical implications that must be conveyed

Structure the output as a list of points, each containing these four elements."""

def get_verification_prompt(translation, key_points):
    return f"""Verify this translation against the key points:

Translation:
{translation}

Key Points:
{json.dumps([point.dict() for point in key_points], indent=2)}

Verify:
    matches_commentary: bool = Field(
        description="Whether the translation fully aligns with all key points from the commentary",
    )
    missing_concepts: str = Field(
        description="List of concepts from commentary that are missing or incorrectly translated",
    )
    misinterpretations: str = Field(
        description="List of any concepts that were translated in ways that contradict the commentary",
    )
    context_accuracy: Dict[str, str] = Field(
        description="Verification of key contextual elements mentioned in commentary",
    )

Provide structured verification results."""

def get_commentary_translation_prompt(sanskrit, source, commentary):
    return f"""As an expert in Tibetan Commentary translation, translate this commentary:
    Sanskrit text:
{sanskrit}
Source Text: {source}
Commentary to translate: {commentary}

Focus on:
- Accurate translation of technical terms
- Preservation of traditional methods
- Proper handling of citations
- Maintaining pedagogical structure
- Correct translation of formal language

Provide only the translated commentary."""

def get_combined_commentary_prompt(source, commentaries):
    return f"""Create a Combined commentary explanation sentence by sentence using these translated commentary of the source text, if there isn't a single commentary then create your own:

Source Text: {source}

{commentaries}
"""

def extract_commentary_key_points(commentary: str) -> List[KeyPoint]:
    """Extract key points from commentary with structured output."""
    prompt = get_key_points_extraction_prompt(commentary)
    result = key_points_extractor.invoke(prompt)
    return result.points

def verify_against_commentary(translation: str, key_points: List[KeyPoint]) -> CommentaryVerification:
    """Verify translation against commentary key points."""
    verification_prompt = get_verification_prompt(translation, key_points)
    verification = llm.with_structured_output(CommentaryVerification).invoke(verification_prompt)
    return verification

def commentary_translator_1(state: State):
    """Translate first commentary with expertise focus."""
    if state['commentary1'] == "":
        return {"commentary1": None, "commentary1_translation": None}
    
    prompt = get_commentary_translation_prompt(state['sanskrit'], state['source'], state['commentary1'])
    commentary_1 = llm.invoke(prompt)
    commentary_1_ = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['commentary1'], commentary_1.content))
    return {"commentary1": commentary_1.content, "commentary1_translation": commentary_1_.extracted_translation}

def commentary_translator_2(state: State):
    """Translate second commentary with philosophical focus."""
    if state['commentary2'] == "":
        return {"commentary2": None, "commentary2_translation": None}
    
    prompt = get_commentary_translation_prompt(state['sanskrit'], state['source'], state['commentary2'])
    commentary_2 = llm.invoke(prompt)
    commentary_2_ = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['commentary2'], commentary_2.content))
    return {"commentary2": commentary_2.content, "commentary2_translation": commentary_2_.extracted_translation}

def commentary_translator_3(state: State):
    """Translate third commentary with traditional focus."""
    if state['commentary3'] == "":
        return {"commentary3": None, "commentary3_translation": None}
    
    prompt = get_commentary_translation_prompt(state['sanskrit'], state['source'], state['commentary3'])
    commentary_3 = llm.invoke(prompt)
    commentary_3_ = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['commentary3'], commentary_3.content))
    return {"commentary3": commentary_3.content, "commentary3_translation": commentary_3_.extracted_translation}

def aggregator(state: State):
    """Combine and analyze all commentaries."""
    combined = (
        f"Source Text: {state['source']}\n\n"
        f"Commentary 1:\n{state['commentary1']}\n\n"
        f"Commentary 2:\n{state['commentary2']}\n\n"
        f"Commentary 3:\n{state['commentary3']}\n\n"
    )
    
    prompt = get_combined_commentary_prompt(state['source'], combined)
    msg = llm.invoke(prompt)
    key_points = extract_commentary_key_points(msg.content)
    
    return {
        "combined_commentary": msg.content,
        "key_points": key_points
    }
