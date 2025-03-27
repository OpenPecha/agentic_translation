from typing import List
from tibetan_translator.models import KeyPoint, State, Translation_extractor, CommentaryPoints
from tibetan_translator.prompts import (
    get_key_points_extraction_prompt,
    get_commentary_translation_prompt,
    get_translation_prompt,
    
)
from tibetan_translator.utils import llm, llm_thinking, get_combined_commentary_prompt, create_source_analysis



def extract_commentary_key_points(commentary: str) -> List[KeyPoint]:
    """Extract key points from commentary with structured output."""
    prompt = get_key_points_extraction_prompt(commentary)
    result = llm.with_structured_output(CommentaryPoints).invoke(prompt)
    return result.points


def commentary_translator_1(state: State):
    """Translate first commentary with expertise focus."""
    if not state['commentary1']:
        return {"commentary1": None, "commentary1_translation": None}
    
    # Pass the target language to the commentary translation prompt
    prompt = get_commentary_translation_prompt(
        state['sanskrit'], 
        state['source'], 
        state['commentary1'],
        language=state.get('language', 'English')
    )
    commentary_1 = llm.invoke(prompt)
    commentary_1_ = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['commentary1'], commentary_1.content))
    return {"commentary1": commentary_1.content, "commentary1_translation": commentary_1_.extracted_translation}


def commentary_translator_2(state: State):
    """Translate second commentary with philosophical focus."""
    if not state['commentary2']:
        return {"commentary2": None, "commentary2_translation": None}
    
    # Pass the target language to the commentary translation prompt
    prompt = get_commentary_translation_prompt(
        state['sanskrit'], 
        state['source'], 
        state['commentary2'],
        language=state.get('language', 'English')
    )
    commentary_2 = llm.invoke(prompt)
    commentary_2_ = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['commentary2'], commentary_2.content))
    return {"commentary2": commentary_2.content, "commentary2_translation": commentary_2_.extracted_translation}


def commentary_translator_3(state: State):
    """Translate third commentary with traditional focus."""
    if not state['commentary3']:
        return {"commentary3": None, "commentary3_translation": None}
    
    # Pass the target language to the commentary translation prompt
    prompt = get_commentary_translation_prompt(
        state['sanskrit'], 
        state['source'], 
        state['commentary3'],
        language=state.get('language', 'English')
    )
    commentary_3 = llm.invoke(prompt)
    commentary_3_ = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['commentary3'], commentary_3.content))
    return {"commentary3": commentary_3.content, "commentary3_translation": commentary_3_.extracted_translation}


def aggregator(state: State):
    """
    Combine commentaries based on the following logic:
    - If no commentaries exist, create source analysis
    - If only one commentary exists, use that as the combined commentary
    - If multiple commentaries exist, use LLM to create a combined commentary
    """
    # Check if any commentaries exist
    has_commentary1 = state.get('commentary1_translation') not in [None, "", "None"]
    has_commentary2 = state.get('commentary2_translation') not in [None, "", "None"]
    has_commentary3 = state.get('commentary3_translation') not in [None, "", "None"]
    
    # Count how many commentaries we have
    commentary_count = sum([has_commentary1, has_commentary2, has_commentary3])
    
    # If no commentaries, create source analysis instead
    if commentary_count == 0:
        source_analysis = create_source_analysis(
            state['source'], 
            state.get('sanskrit', ''), 
            language=state.get('language', 'English')
        )
        return {
            "combined_commentary": source_analysis,
            "commentary_source": "source_analysis"
        }
    
    # If only one commentary, use that as the combined
    if commentary_count == 1:
        if has_commentary1:
            return {"combined_commentary": state['commentary1_translation'], "commentary_source": "traditional"}
        elif has_commentary2:
            return {"combined_commentary": state['commentary2_translation'], "commentary_source": "traditional"}
        else:  # has_commentary3 must be True
            return {"combined_commentary": state['commentary3_translation'], "commentary_source": "traditional"}
    
    # If we have multiple commentaries, combine them using LLM
    combined = ""
    if has_commentary1:
        combined += f"Commentary 1:\n{state['commentary1_translation']}\n\n"
    if has_commentary2:
        combined += f"Commentary 2:\n{state['commentary2_translation']}\n\n"
    if has_commentary3:
        combined += f"Commentary 3:\n{state['commentary3_translation']}\n\n"
    
    # Get the target language
    language = state.get('language', 'English')
    
    # Create the prompt for multiple commentaries
    prompt_messages = get_combined_commentary_prompt(
        source_text=state['source'], 
        commentaries=combined,
        has_commentaries=True,  # We know we have commentaries
        language=language
    )
    
    # Use the thinking LLM for analysis
    response = llm_thinking.invoke(prompt_messages)
    
    # Extract content from thinking response
    commentary_content = ""
    
    if isinstance(response, list):
        # Handle thinking output format, extracting only the text part
        for chunk in response:
            if isinstance(chunk, dict) and chunk.get('type') == 'text':
                commentary_content = chunk.get('text', '')
    elif hasattr(response, 'content'):
        if isinstance(response.content, list) and len(response.content) > 1:
            # Extract text from the second element (typical thinking response structure)
            commentary_content = response.content[1].get('text', '')
        else:
            commentary_content = response.content
    else:
        commentary_content = str(response)
    
    return {"combined_commentary": commentary_content, "commentary_source": "traditional"}