from tibetan_translator.models import State, Translation_extractor,Translation
from tibetan_translator.prompts import (
    get_formatting_feedback_prompt,
    get_translation_prompt
)
from tibetan_translator.utils import llm


def formater(state: State): 
    """Format the translation to match the source text's structure."""
    prompt = get_formatting_feedback_prompt(
        state['source'], state['translation'][-1], state['format_feedback_history'],
        language=state.get('language', 'English')
    )
    msg = llm.invoke(prompt)
    formatted_translation = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['source'], msg.content))
    
    state["translation"].append(formatted_translation.extracted_translation)
    return {
        "translation": state["translation"],
        # Make sure to preserve plaintext_translation
        "plaintext_translation": state.get("plaintext_translation", "")
    }


def format_evaluator_feedback(state: State):
    """Evaluate and maintain translation formatting."""
    prompt = get_formatting_feedback_prompt(
        state['source'], state['translation'][-1], state['format_feedback_history'],
        language=state.get('language', 'English')
    )
    review = llm.with_structured_output(Translation).invoke(prompt)
    
    if review.format_matched:
        return {
            "formated": True, 
            "translation": state['translation'],
            # Make sure to preserve plaintext_translation
            "plaintext_translation": state.get("plaintext_translation", "")
        }
    
    state["format_feedback_history"].append(f"Formatting issue: {review.feedback_format}")
    return {
        "formated": False, 
        "translation": state['translation'], 
        "format_feedback_history": state["format_feedback_history"],
        "format_iteration": state.get("format_iteration", 0) + 1,
        # Make sure to preserve plaintext_translation
        "plaintext_translation": state.get("plaintext_translation", "")
    }
