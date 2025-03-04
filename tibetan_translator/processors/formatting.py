from tibetan_translator.models import State, Translation_extractor
from tibetan_translator.prompts import (
    get_formatting_feedback_prompt,
    get_translation_prompt
)
from tibetan_translator.utils import llm


def formater(state: State): 
    """Format the translation to match the source text's structure."""
    prompt = get_formatting_feedback_prompt(state['source'], state['translation'][-1], state['format_feedback_history'])
    msg = llm.invoke(prompt)
    formatted_translation = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['source'], msg.content))
    
    state["translation"].append(formatted_translation.extracted_translation)
    return {"translation": state["translation"]}


def format_evaluator_feedback(state: State):
    """Evaluate and maintain translation formatting."""
    prompt = get_formatting_feedback_prompt(state['source'], state['translation'][-1], state['format_feedback_history'])
    review = llm.invoke(prompt)
    
    if review.format_matched:
        return {"formated": True, "translation": state['translation']}
    
    state["format_feedback_history"].append(f"Formatting issue: {review.feedback_format}")
    return {"formated": False, "translation": state['translation'], "format_feedback_history": state["format_feedback_history"], "itteration": state["itteration"]+1}
