from tibetan_translator.models import State, Feedback, CommentaryVerification, LanguageCheck
from tibetan_translator.prompts import (
    get_verification_prompt,
    get_translation_evaluation_prompt,
    get_language_check_prompt
)
from tibetan_translator.utils import llm, llm_thinking, dict_to_text
from tibetan_translator.config import MAX_FORMAT_ITERATIONS


def verify_against_commentary(translation: str, combined_commentary: str, language: str = "English") -> CommentaryVerification:
    """Verify translation against commentary."""
    verification_prompt = get_verification_prompt(translation, combined_commentary, language=language)
    # Use standard llm with structured output since thinking doesn't support structured output
    verification = llm.with_structured_output(CommentaryVerification).invoke(verification_prompt)
    return verification


def check_translation_language(translation: str, language: str = "English") -> LanguageCheck:
    """Check if the translation is in the target language."""
    language_check_prompt = get_language_check_prompt(translation, language=language)
    language_check = llm.with_structured_output(LanguageCheck).invoke(language_check_prompt)
    return language_check

def llm_call_evaluator(state: State):
    """Evaluate translation quality AND formatting with comprehensive verification."""
    previous_feedback = "\n".join(state["feedback_history"]) if state["feedback_history"] else "No prior feedback."
    
    language = state.get('language', 'English')
    
    # First check if the translation is in the target language
    language_check = check_translation_language(state['translation'][-1], language=language)
    
    # If not in target language, return early with language issue feedback
    if not language_check.is_target_language:
        language_feedback = f"WRONG LANGUAGE: Translation is not in {language}. {language_check.language_issues}"
        feedback_entry = f"Iteration {state['itteration']} - LANGUAGE ERROR\n"
        feedback_entry += f"In Target Language: False\n"
        feedback_entry += f"Language Issues: {language_check.language_issues}\n"
        
        return {
            "is_target_language": False,
            "language_issues": language_check.language_issues,
            "grade": "bad",
            "formated": False,
            "feedback_history": state["feedback_history"] + [feedback_entry],
        }
    
    # Only proceed with full evaluation if language is correct
    try:
        verification = verify_against_commentary(
            state['translation'][-1], 
            state['combined_commentary'],
            language=language
        )
    except Exception as e:
        print(f"Verification error: {e}")
        verification = verify_against_commentary(
            state['translation'][-1], 
            state['combined_commentary'],
            language=language
        )
        
    prompt = get_translation_evaluation_prompt(
        state['source'], state['translation'][-1], state['combined_commentary'], 
        verification, previous_feedback, 
        language=state.get('language', 'English')
    )
    
    # Use standard llm with structured output for combined evaluation
    evaluation = llm.with_structured_output(Feedback).invoke(prompt)
    
    # Create comprehensive feedback entry with both content and formatting feedback
    feedback_entry = f"Iteration {state['itteration']} - Grade: {evaluation.grade}\n"
    feedback_entry += f"In Target Language: {evaluation.is_target_language}\n"
    feedback_entry += f"Format Matched: {evaluation.format_matched}\n"
    
    if not evaluation.is_target_language:
        feedback_entry += f"Language Issues: {evaluation.language_issues}\n"
    
    if evaluation.format_issues:
        feedback_entry += f"Format Issues: {evaluation.format_issues}\n"
    
    feedback_entry += f"Content Feedback: {evaluation.feedback}\n"
    
    return {
        "is_target_language": evaluation.is_target_language,
        "language_issues": evaluation.language_issues,
        "grade": evaluation.grade,
        "formated": evaluation.format_matched,  # Update the formatted status directly
        "feedback_history": state["feedback_history"] + [feedback_entry],
        # Preserve format-specific feedback for reference
        "format_feedback_history": state.get("format_feedback_history", []) + 
                                  ([evaluation.format_issues] if evaluation.format_issues else [])
    }


def route_structured(state: State):
    """Route based on language and formatting evaluation results."""
    # First check if the translation is in the target language
    if state.get("is_target_language") is False:
        return "Wrong Language"
    
    # Then check formatting
    if state['formated']:
        return "Accepted"
    elif state.get("format_iteration", 0) >= MAX_FORMAT_ITERATIONS:  # Use format_iteration for formatting loop
        return "Accepted"
    return "Rejected + Feedback"
