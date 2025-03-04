from typing import List
from tibetan_translator.models import KeyPoint, State
from tibetan_translator.prompts import (
    get_key_points_extraction_prompt,
    get_commentary_translation_prompt,
    get_translation_prompt,
    get_combined_commentary_prompt
)
from tibetan_translator.utils import llm


def extract_commentary_key_points(commentary: str) -> List[KeyPoint]:
    """Extract key points from commentary with structured output."""
    prompt = get_key_points_extraction_prompt(commentary)
    result = llm.with_structured_output(KeyPoint).invoke(prompt)
    return result.points


def commentary_translator_1(state: State):
    """Translate first commentary with expertise focus."""
    if not state['commentary1']:
        return {"commentary1": None, "commentary1_translation": None}
    
    prompt = get_commentary_translation_prompt(state['sanskrit'], state['source'], state['commentary1'])
    commentary_1 = llm.invoke(prompt)
    commentary_1_ = llm.with_structured_output(KeyPoint).invoke(get_translation_prompt(state['commentary1'], commentary_1.content))
    return {"commentary1": commentary_1.content, "commentary1_translation": commentary_1_.extracted_translation}


def commentary_translator_2(state: State):
    """Translate second commentary with philosophical focus."""
    if not state['commentary2']:
        return {"commentary2": None, "commentary2_translation": None}
    
    prompt = get_commentary_translation_prompt(state['sanskrit'], state['source'], state['commentary2'])
    commentary_2 = llm.invoke(prompt)
    commentary_2_ = llm.with_structured_output(KeyPoint).invoke(get_translation_prompt(state['commentary2'], commentary_2.content))
    return {"commentary2": commentary_2.content, "commentary2_translation": commentary_2_.extracted_translation}


def commentary_translator_3(state: State):
    """Translate third commentary with traditional focus."""
    if not state['commentary3']:
        return {"commentary3": None, "commentary3_translation": None}
    
    prompt = get_commentary_translation_prompt(state['sanskrit'], state['source'], state['commentary3'])
    commentary_3 = llm.invoke(prompt)
    commentary_3_ = llm.with_structured_output(KeyPoint).invoke(get_translation_prompt(state['commentary3'], commentary_3.content))
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