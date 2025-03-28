import json
import logging
from typing import List, Literal, TypedDict, Any, Union
from pydantic import BaseModel, Field, field_validator

# Setup model-specific logger
logger = logging.getLogger("tibetan_translator.models")

class CommentaryVerification(BaseModel):
    matches_commentary: bool = Field(
        description="Whether the translation fully aligns with all key points from the commentary",
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
# Add new model for glossary entries
class GlossaryEntry(BaseModel):
    tibetan_term: str = Field(description="Original Tibetan term")
    translation: str = Field(description="Exact translation used in the target language")
    context: str = Field(description="Context or usage notes in the target language")
    entity_category: str = Field(description="Entity category (e.g., person, place, etc.) in the target language, if not entity then leave it blank")
    commentary_reference: str = Field(description="Reference to commentary explanation in the target language")
    category: str = Field(description="Term category (philosophical, technical, etc.) in the target language")

class GlossaryExtraction(BaseModel):
    entries: List[GlossaryEntry] = Field(description="List of extracted glossary entries")
    
    @field_validator('entries', mode='before')
    @classmethod
    def validate_entries(cls, v: Any) -> List[GlossaryEntry]:
        """Validator to handle string inputs for entries field.
        
        This is especially important for Chinese and other non-Latin languages where
        JSON parsing might return a string instead of properly parsing to a list.
        """
        logger.debug(f"GlossaryExtraction validator received entries of type: {type(v)}")
        
        # If it's already a list, return it
        if isinstance(v, list):
            logger.debug(f"Entries is already a list with {len(v)} items")
            return v
            
        # If it's a string, try to parse it as JSON
        if isinstance(v, str):
            logger.debug(f"Entries is a string, attempting to parse as JSON. Content sample: {v[:200]}...")
            try:
                parsed = json.loads(v)
                logger.debug(f"Successfully parsed string to {type(parsed)}")
                
                # If parsing gave us a list, return it
                if isinstance(parsed, list):
                    logger.debug(f"Parsed to a list with {len(parsed)} items")
                    return parsed
                else:
                    logger.error(f"Parsed JSON is not a list but {type(parsed)}")
                    raise ValueError(f"Expected a list after parsing string, got {type(parsed)}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse entries string as JSON: {str(e)}")
                raise ValueError(f"Invalid JSON string for entries: {str(e)}")
        
        # If we got here, it's neither a list nor a string that parses to a list
        logger.error(f"Invalid type for entries: {type(v)}")
        raise ValueError(f"entries must be a list or a string containing a JSON list, got {type(v)}")

class LanguageCheck(BaseModel):
    is_target_language: bool = Field(
        description="Whether the translation is actually in the specified target language",
    )
    language_issues: str = Field(
        description="Description of any issues with the target language if not in target language",
        default="",
    )

class Feedback(BaseModel):
    is_target_language: bool = Field(
        description="Whether the translation is actually in the specified target language",
        default=True,
    )
    language_issues: str = Field(
        description="Description of any issues with the target language if not in target language",
        default="",
    )
    grade: Literal["bad", "okay", "good", "great"] = Field(
        description="Evaluate translation quality based on accuracy and commentary alignment",
    )
    feedback: str = Field(
        description="Detailed feedback on improving translation based on commentary interpretation",
    )
    format_matched: bool = Field(
        description="Whether the translation structure matches the source structure (line count, verse form, paragraph breaks)",
        default=False,
    )
    format_issues: str = Field(
        description="Specific formatting issues to address (if any)",
        default="",
    )

class Translation_extractor(BaseModel):
    extracted_translation: str = Field("extracted translation with exact format from the Respond")
class Translation(BaseModel):
    format_matched: bool = Field(
        description="Evaluate if translation preserves source text's formatting such as linebreaks",
    )
    extracted_translation: str = Field(
        description="The translation maintaining all original formatting",
    )
    feedback_format: str = Field(
        description="Detailed guidance on matching source text formatting and only the formating",
    )


class KeyPoint(BaseModel):
    concept: str = Field(description="Core concept or interpretation")
    terminology: List[str] = Field(description="Required terminology")
    context: str = Field(description="Required contextual information")
    implications: List[str] = Field(description="Philosophical implications")

class CommentaryPoints(BaseModel):
    points: List[KeyPoint] = Field(description="List of key points from commentary")


class State(TypedDict):
    translation: List[str]
    commentary1_translation: str
    commentary2_translation: str
    commentary3_translation: str
    source: str
    sanskrit: str
    language: str
    feedback_history: List[str]
    format_feedback_history: List[str]
    commentary1: str
    commentary2: str
    commentary3: str
    combined_commentary: str
    commentary_source: str  # Tracks origin of commentary: "traditional" or "source_analysis"
    key_points: List[KeyPoint]
    plaintext_translation: str  
    itteration: int  # For translation quality improvement iterations
    format_iteration: int  # For formatting correction iterations
    formated: bool
    glossary: List[GlossaryEntry]
    plaintext_translation: str
