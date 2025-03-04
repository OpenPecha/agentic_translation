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
    translation: str = Field(description="Exact English translation used in the translation")
    context: str = Field(description="Context or usage notes")
    entity_category: str = Field(description="entity category (e.g., person, place, etc.), if not entity then leave it blank")
    commentary_reference: str = Field(description="Reference to commentary explanation")
    category: str = Field(description="Term category (philosophical, technical, etc.)")

class GlossaryExtraction(BaseModel):
    entries: List[GlossaryEntry] = Field(description="List of extracted glossary entries")

class Feedback(BaseModel):
    grade: Literal["bad", "okay", "good", "great"] = Field(
        description="Evaluate translation quality based on accuracy and commentary alignment",
    )
    feedback: str = Field(
        description="Detailed feedback on improving translation based on commentary interpretation",
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
    key_points: List[KeyPoint]
    itteration: int
    formated: bool
    glossary: List[GlossaryEntry]
    plaintext_translation: str
