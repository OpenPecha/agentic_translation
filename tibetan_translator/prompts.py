
from tibetan_translator.models import KeyPoint, State
from typing import List
from tibetan_translator.models import CommentaryVerification, Translation_extractor
import json
from tibetan_translator.utils import llm

def get_translation_prompt(source, example):
    # This is kept for backward compatibility
    # New code should use utils.get_translation_extraction_prompt instead
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

def get_verification_prompt(translation, combined_commentary, language="English"):
    """Get prompt to verify translation against commentary."""
    return f"""Verify this translation against the commentary:

Translation:
{translation}

Commentary (Including Analysis):
{combined_commentary}

Verify:
    matches_commentary: bool = Field(
        description="Whether the translation fully aligns with the commentary",
    )
    missing_concepts: str = Field(
        description="List of concepts from commentary that are missing or incorrectly translated",
    )
    misinterpretations: str = Field(
        description="List of any concepts that were translated in ways that contradict the commentary",
    )
    context_accuracy: str = Field(
        description="Verification of key contextual elements mentioned in commentary",
    )

Important: Your verification MUST be in {language}. Provide all feedback, descriptions, and analyses in {language}.

Provide structured verification results."""

def get_commentary_translation_prompt(sanskrit, source, commentary, language="English"):
    return f"""As an expert in Tibetan Commentary translation\\\, translate this commentary into {language}:
    Sanskrit text:
{sanskrit}
Source Text: {source}
Commentary to translate: {commentary}

Focus on:
- Accurate translation of technical terms into {language}
- Preservation of traditional methods
- Proper handling of citations
- Maintaining pedagogical structure
- Correct translation of formal language
- Ensure all terminology is translated into {language}

Provide only the translated commentary in {language}."""

# This prompt is deprecated - use get_combined_commentary_prompt from utils.py instead
# def get_combined_commentary_prompt(source, commentaries, language="English"):
#     """This function is deprecated. Use utils.get_combined_commentary_prompt instead."""
#     return f"""Create a Combined commentary explanation sentence by sentence using these translated commentary of the source text, if there isn't a single commentary then create your own.

# Source Text: {source}

# {commentaries}

# Important: Your combined commentary MUST be in {language}. Ensure all terminology, explanations, and analyses are expressed in {language}.
# """


def get_language_check_prompt(translation, language="English"):
    """Generate a prompt to verify if a translation is in the target language."""
    return f"""Verify if this text is actually written in {language}:

Translation to check:
{translation}

CRITICAL TASK:
1. First, determine if this text is primarily written in {language}
2. Check for any sections that might be in a different language
3. Verify that technical terms are appropriately handled in {language}

Your response must provide:
1. is_target_language: Whether the text is actually in {language} (true/false)
2. language_issues: If not in {language}, describe what language it appears to be in and any specific issues

IMPORTANT: This check is only about the language used, not about translation quality or correctness.
"""

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

CRITICAL VERIFICATION STEPS:
1. FIRST, verify the translation is actually written in {language}, not in another language
2. If not in {language}, stop evaluation and report the language issues
3. Only if confirmed to be in {language}, proceed with full evaluation

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
1. Whether the translation is actually in {language} (true/false)
2. If not in {language}, details about language issues
3. A grade (great/good/okay/bad)
4. Whether the format matches the source structure (true/false)
5. Specific formatting issues (if any)
6. {language}-specific linguistic feedback (focus on naturalness, fluency, and accuracy)
7. Detailed content feedback for improvements

IMPORTANT: Your evaluation MUST be in {language}. Provide all feedback in {language} with specific suggestions for how to improve the translation's fluency and naturalness in {language}.

Formatting issues, incorrect structure, and unnatural language are ALL CRITICAL problems that must be fixed for a translation to be acceptable."""
def get_translation_improvement_prompt(sanskrit, source, combined_commentary, latest_feedback, current_translation, language="English"):
    """Generate a prompt for improving a translation based on feedback."""
    return f"""Create an improved {language} translation that addresses the previous feedback:

Sanskrit text:
{sanskrit}

Source Text:
{source}

Commentary Analysis:
{combined_commentary}

Latest Feedback to Address:
{latest_feedback}

Current Translation:
{current_translation}

LINGUISTIC REQUIREMENTS FOR {language.upper()}:
- Your translation MUST be in fluent, natural {language}
- Use appropriate {language} grammar, syntax, and idiomatic expressions
- Maintain proper {language} sentence structure and flow
- Use culturally-appropriate and accurate terminology in {language}
- Avoid awkward phrasing, word-for-word translations, or unnatural constructions
- Technical Buddhist terms should be translated using established {language} conventions when available

IMPROVEMENT REQUIREMENTS:
1. Make specific improvements based on the latest feedback while keeping the translation close to the source text
2. Ensure alignment with the commentary analysis
3. Focus on addressing each point of criticism, especially regarding linguistic fluency
4. Maintain accuracy while implementing the suggested changes
5. Refer to the Sanskrit text as well as the Tibetan text, as the Tibetan text itself is translated from the Sanskrit text
6. Use the analysis section in the commentary for deeper understanding of Buddhist concepts
7. Pay special attention to making the translation sound natural in {language} for native speakers

IMPORTANT: Generate ONLY the improved translation in fluent, natural {language}. Do not include explanations or notes.

Your translation should preserve the original meaning but express it in a way that sounds completely natural to native {language} speakers."""
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
def get_formatting_feedback_prompt(source, translation, previous_feedback, language="English"):
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
2. Do not add "།" in the {language} translation.
3. Provide specific formatting guidance based on previous feedback.
4. Ensure the format matches the source text.

Provide specific formatting feedback."""
def get_glossary_extraction_prompt(source, combined_commentary, final_translation, language="English", commentary_source="traditional"):
    """Generate a prompt for extracting glossary terms from a translation."""
    
    # Customize commentary reference instructions based on source
    if commentary_source == "source_analysis":
        commentary_reference_instr = f"Commentary reference (IMPORTANT: Since this translation was based on direct source analysis rather than traditional commentaries, indicate this by starting with 'From source analysis:'(in {language} !!) followed by relevant linguistic or structural insights in {language})"
    else:
        commentary_reference_instr = f"Commentary reference (IMPORTANT: This MUST be written in {language}, referencing traditional commentary explanations)"
    
    return f"""
Extract a comprehensive glossary from the final {language} translation only:

Source Text:
{source}

{"Source Analysis:" if commentary_source == "source_analysis" else "Combined Commentary:"}
{combined_commentary}

Final Translation:
{final_translation}

For each technical term, provide:
1. Original Tibetan term in the Source Text
2. Exact {language} translation term used
3. Usage context (IMPORTANT: This MUST be written in {language})
4. {commentary_reference_instr}
5. Term category (e.g., philosophical, technical, ritual, doctrinal) (In {language})
6. Entity category (e.g., person, place, etc.), if not entity then leave it blank

Focus on:
- Buddhist terms
- Important Entities (names of people, places, etc.)
- Specialized vocabulary in Buddhist Texts
- Do not use any terms that are not in the Source text
- {"Only refer to the source analysis for linguistic insights" if commentary_source == "source_analysis" else "Do not use any terms from the Commentary unless it overlaps with the Source text"}

CRITICAL INSTRUCTIONS:
- ALL descriptions, context, explanations, and categorical information MUST be in {language}
- DO NOT provide any content in English unless the target language is English
- The only field that should not be in {language} is the original Tibetan term
- {"For commentary_reference fields, always start with 'From source analysis:' to indicate this was not from traditional commentaries" if commentary_source == "source_analysis" else ""}

OUTPUT FORMAT REQUIREMENTS:
- You MUST structure your output as valid, properly formatted JSON
- The output MUST be a JSON array (list) of objects
- Each object MUST have exactly these fields: tibetan_term, translation, context, commentary_reference, category, entity_category
- No extra fields or comments outside the JSON structure are allowed
- For ALL languages including Chinese, Japanese, Korean, etc., ensure the JSON is properly formatted with correct delimiters

Example of the required JSON structure:
```json
[
  {{
    "tibetan_term": "བྱང་ཆུབ་སེམས",
    "translation": "bodhicitta",
    "context": "The mind of enlightenment",
    "commentary_reference": "{f"From source analysis: Term identified as key philosophical concept in Buddhist soteriology" if commentary_source == "source_analysis" else "From Śāntideva's explanation"}",
    "category": "philosophical",
    "entity_category": ""
  }},
  {{
    "tibetan_term": "ཤེས་རབ",
    "translation": "wisdom",
    "context": "Transcendent understanding",
    "commentary_reference": "{f"From source analysis: Linguistic analysis shows connection to Sanskrit prajñā" if commentary_source == "source_analysis" else "In context of perfections"}",
    "category": "philosophical",
    "entity_category": ""
  }}
]
```

IMPORTANT: 
1. The output MUST ONLY contain the JSON array - no other text
2. The JSON must be valid and properly formatted
3. All field contents in {language} (except the tibetan_term)
4. Even for Chinese, Japanese, Korean and other non-Latin languages, preserve the JSON structure exactly as shown
5. Do not add any text before or after the JSON array"""