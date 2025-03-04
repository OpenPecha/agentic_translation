import pandas as pd
from typing import List
from tibetan_translator.models import State, GlossaryEntry, GlossaryExtraction
from tibetan_translator.prompts import get_glossary_extraction_prompt
from tibetan_translator.utils import llm


def extract_glossary(state: State) -> List[GlossaryEntry]:
    """Extract technical terms and their translations into a glossary."""
    glossary_prompt = get_glossary_extraction_prompt(
        state['source'], state['combined_commentary'], state['translation'][-1]
    )
    extractor = llm.with_structured_output(GlossaryExtraction)
    result = extractor.invoke(glossary_prompt)
    return result.entries


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


def generate_glossary(state: State):
    """Generate glossary and save to CSV."""
    entries = extract_glossary(state)
    filename = generate_glossary_csv(entries)
    return {"glossary": entries}
