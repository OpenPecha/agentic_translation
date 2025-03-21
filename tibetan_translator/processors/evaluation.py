from tibetan_translator.models import State, Feedback, CommentaryVerification
from tibetan_translator.prompts import (
    get_verification_prompt,
    get_translation_evaluation_prompt
)
from tibetan_translator.utils import llm, llm_thinking, dict_to_text
from tibetan_translator.config import MAX_FORMAT_ITERATIONS


def verify_against_commentary(translation: str, combined_commentary: str, language: str = "English") -> CommentaryVerification:
    """Verify translation against commentary."""
    verification_prompt = get_verification_prompt(translation, combined_commentary, language=language)
    # Use standard llm with structured output since thinking doesn't support structured output
    verification = llm.with_structured_output(CommentaryVerification).invoke(verification_prompt)
    return verification


def llm_call_evaluator(state: State):
    """Evaluate translation quality AND formatting with comprehensive verification."""
    previous_feedback = "\n".join(state["feedback_history"]) if state["feedback_history"] else "No prior feedback."
    
    language = state.get('language', 'English')
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
    feedback_entry += f"Format Matched: {evaluation.format_matched}\n"
    
    if evaluation.format_issues:
        feedback_entry += f"Format Issues: {evaluation.format_issues}\n"
    
    feedback_entry += f"Content Feedback: {evaluation.feedback}\n"
    
    return {
        "grade": evaluation.grade,
        "formated": evaluation.format_matched,  # Update the formatted status directly
        "feedback_history": state["feedback_history"] + [feedback_entry],
        # Preserve format-specific feedback for reference
        "format_feedback_history": state.get("format_feedback_history", []) + 
                                  ([evaluation.format_issues] if evaluation.format_issues else [])
    }


def route_structured(state: State):
    """Route based on formatting evaluation results."""
    if state['formated']:
        return "Accepted"
    elif state.get("format_iteration", 0) >= MAX_FORMAT_ITERATIONS:  # Use format_iteration for formatting loop
        return "Accepted"
    return "Rejected + Feedback"
