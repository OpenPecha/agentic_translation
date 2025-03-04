from tibetan_translator.models import State, Feedback, CommentaryVerification
from tibetan_translator.prompts import (
    get_verification_prompt,
    get_translation_evaluation_prompt
)
from tibetan_translator.utils import llm, dict_to_text


def verify_against_commentary(translation: str, key_points: list) -> CommentaryVerification:
    """Verify translation against commentary key points."""
    verification_prompt = get_verification_prompt(translation, key_points)
    verification = llm.with_structured_output(CommentaryVerification).invoke(verification_prompt)
    return verification


def llm_call_evaluator(state: State):
    """Evaluate translation quality with commentary verification."""
    previous_feedback = "\n".join(state["feedback_history"]) if state["feedback_history"] else "No prior feedback."
    
    try:
        verification = verify_against_commentary(state['translation'][-1], state['key_points'])
    except:
        verification = verify_against_commentary(state['translation'][-1], state['key_points'])
        
    prompt = get_translation_evaluation_prompt(
        state['source'], state['translation'][-1], state['combined_commentary'], state['key_points'], verification, previous_feedback
    )
    
    grade = llm.with_structured_output(Feedback).invoke(prompt)
    feedback_entry = f"Iteration {state['itteration']} - Grade: {grade.grade}\nFeedback: {grade.feedback}\n"
    
    return {
        "grade": grade.grade,
        "feedback_history": state["feedback_history"] + [feedback_entry]
    }


def route_structured(state: State):
    """Route based on evaluation results."""
    if state['formated']:
        return "Accepted"
    elif state["itteration"] > 6:
        return "Accepted"
    return "Rejected + Feedback"
