
from tibetan_translator.models import KeyPoint, State
from typing import List
from tibetan_translator.models import CommentaryVerification, Translation_extractor
import json
from tibetan_translator.utils import llm

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


def get_translation_evaluation_prompt(source, translation, combined_commentary, key_points, verification, previous_feedback):
    """Generate a prompt for evaluating a translation against commentary and key points."""
    return f"""Evaluate this translation comprehensively:

Source Text: {source}
Target Language: English
Translation: {translation}

Commentary:
{combined_commentary}

Previous Feedback:
{previous_feedback}

Verification Results:
{verification}

Evaluate based on:
1. Commentary alignment
2. Key point representation
3. Technical terminology
4. Philosophical accuracy
5. Whether the sentences match the format of the source text
6. Contextual preservation
7. If the source is in verse, then the translation should be in verse

Grade criteria:
- "great": Perfect alignment with commentary and source text
- "good": Minor deviations
- "okay": Several misalignments
- "bad": Major divergence

Provide specific feedback for improvements."""
def get_translation_improvement_prompt(sanskrit, source, combined_commentary, key_points, latest_feedback, current_translation):
    """Generate a prompt for improving a translation based on feedback."""
    return f"""Create an improved English translation that addresses the previous feedback:

Sanskrit text:
{sanskrit}

Source Text:
{source}

Commentary Analysis:
{combined_commentary}

Key Points:
{key_points}

Latest Feedback to Address:
{latest_feedback}

Current Translation:
{current_translation}

Requirements:
1. Make specific improvements based on the latest feedback while keeping the translation close to the source text.
2. Ensure alignment with the commentary and key points.
3. Focus on addressing each point of criticism.
4. Maintain accuracy while implementing the suggested changes.
5. Refer to the Sanskrit text as well as the Tibetan text, as the Tibetan text itself is translated from the Sanskrit text.

Generate only the improved translation."""
def get_initial_translation_prompt(sanskrit, source, combined_commentary, key_points):
    """Generate a prompt for the initial translation of a Tibetan Buddhist text."""
    return f"""
Translate this Tibetan Buddhist text into English:

Sanskrit text:
{sanskrit}

Source Text:
{source}

Context:
{combined_commentary}

Key Points:
{key_points}

Translation guidance:
- Freely restructure sentences to achieve natural English expression
- Prioritize accuracy of Buddhist concepts and doctrinal meaning
- Preserve all content and implied meanings from the original
- Choose the best way to convey the intended meaning
- Refer to the Sanskrit text as well as the Tibetan text, as the Tibetan text is translated from the Sanskrit text
- The translation should be detailed and should not be in verse format while avoiding adding any extra information
- The translation is not an explanation of the text but a direct translation of the text

Generate the translation in a clear and structured format."""
def get_formatting_feedback_prompt(source, translation, previous_feedback):
    """Generate a prompt to evaluate and improve translation formatting."""
    return f"""Analyze the formatting of this translation:

Source Text:
{source}

Translation:
{translation}

Previous Feedback:
{previous_feedback}

Notes for evaluation:
1. Your task is to evaluate the format, not the translation quality.
2. Do not add "།" in the English translation.
3. Provide specific formatting guidance based on previous feedback.
4. Ensure the format matches the source text.

Provide specific formatting feedback."""
def get_glossary_extraction_prompt(source, combined_commentary, final_translation):
    """Generate a prompt for extracting glossary terms from a translation."""
    return f"""
Extract a comprehensive glossary from the final translation only:

Source Text:
{source}

Combined Commentary:
{combined_commentary}

Final Translation:
{final_translation}

For each technical term, provide:
1. Original Tibetan term in the Source Text
2. Exact Translation term used
3. Usage context
4. Commentary reference
5. Term category (e.g., philosophical, technical, ritual, doctrinal)
6. Entity category (e.g., person, place, etc.), if not entity then leave it blank

Focus on:
- Buddhist terms
- Important Entities (names of people, places, etc.)
- Specialized vocabulary in Buddhist Texts
- Do not use any terms that are not in the Source text
- Do not use any terms from the Commentary unless it overlaps with the Source text

Format the extracted glossary in a structured data format."""