from typing import List
from tibetan_translator.models import State, Translation_extractor
from tibetan_translator.prompts import (
    get_translation_evaluation_prompt,
    get_translation_improvement_prompt,
    get_initial_translation_prompt,
    get_translation_prompt
)
from tibetan_translator.utils import llm


def translation_generator(state: State):
    """Generate improved translation based on commentary and feedback."""
    previous_feedback = "\n".join(state["feedback_history"]) if state["feedback_history"] else "No prior feedback."
    current_iteration = state.get("itteration", 0)

    if state.get("feedback_history"):
        latest_feedback = state["feedback_history"][-1] if state["feedback_history"] else "No feedback yet."
        prompt = get_translation_improvement_prompt(
            state['sanskrit'], state['source'], state['combined_commentary'], state['key_points'], latest_feedback, state['translation'][-1]
        )
        msg = llm.invoke(prompt)
        translation = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['source'], msg.content))
        return {
            "translation": state["translation"] + [translation.extracted_translation],
            "itteration": current_iteration + 1
        }
    else:
        prompt = get_initial_translation_prompt(state['sanskrit'], state['source'], state['combined_commentary'], state['key_points'])
        msg = llm.invoke(prompt)
        translation = llm.with_structured_output(Translation_extractor).invoke(get_translation_prompt(state['source'], msg.content))
        return {
            "translation": [translation.extracted_translation],
            "feedback_history": [f"Iteration {current_iteration} - Initial Translation:\n{msg.content}\n"],
            "iteration": 1
        }


def route_translation(state: State):
    """Route based on translation quality."""
    if state["grade"] == "great":
        return "Accepted"
    elif state["itteration"] >= 4:
        return "Accepted"
    else:
        return "Rejected + Feedback"
