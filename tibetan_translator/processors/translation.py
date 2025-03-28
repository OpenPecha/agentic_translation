from typing import List
from tibetan_translator.models import State, Translation_extractor
from tibetan_translator.prompts import (
    get_translation_evaluation_prompt,
    get_translation_improvement_prompt,
    get_initial_translation_prompt,
    get_translation_prompt
)
from tibetan_translator.utils import (
    llm, 
    llm_thinking, 
    get_translation_extraction_prompt, 
    get_plain_translation_prompt, 
    get_enhanced_translation_prompt
)
from tibetan_translator.config import MAX_TRANSLATION_ITERATIONS


def translation_generator(state: State):
    """Generate improved translation based on commentary and feedback."""
    previous_feedback = "\n".join(state["feedback_history"]) if state["feedback_history"] else "No prior feedback."
    current_iteration = state.get("itteration", 0)

    if state.get("feedback_history"):
        latest_feedback = state["feedback_history"][-1] if state["feedback_history"] else "No feedback yet."
        target_language = state.get('language', 'English')
        
        prompt = get_translation_improvement_prompt(
            state['sanskrit'], state['source'], state['combined_commentary'], 
            latest_feedback, state['translation'][-1],
            language=target_language
        )
        # Use standard llm for subsequent iterations
        msg = llm.invoke(prompt)
        translation = llm.with_structured_output(Translation_extractor).invoke(
            get_translation_extraction_prompt(state['source'], msg.content, language=target_language)
        )
        return {
            "translation": state["translation"] + [translation.extracted_translation],
            "itteration": current_iteration + 1
        }
    else:
        # Check if we're using source analysis mode (no commentaries)
        is_source_focused = not state.get('commentary1') and not state.get('commentary2') and not state.get('commentary3')
        
        # Select the appropriate translation prompt based on mode
        if is_source_focused:
            # Use enhanced translation prompt for source-focused translation
            prompt = get_enhanced_translation_prompt(
                state['sanskrit'], 
                state['source'], 
                state['combined_commentary'],  # This now contains source analysis
                language=state.get('language', 'English')
            )
        else:
            # Use standard commentary-based translation prompt
            prompt = get_initial_translation_prompt(
                state['sanskrit'], 
                state['source'], 
                state['combined_commentary'], 
                language=state.get('language', 'English')
            )
        
        # Use thinking LLM for primary translation
        thinking_response = llm_thinking.invoke(prompt)
        
        # Extract content and thinking from thinking response
        translation_content = ""
        thinking_content = ""
        
        # Handle llm_thinking response structure which is typically:
        # [{'signature': '...', 'thinking': '...', 'type': 'thinking'}, 
        #  {'text': '...', 'type': 'text'}]
        if isinstance(thinking_response, list):
            # Just extract the text portion (second dictionary with text key)
            for chunk in thinking_response:
                if isinstance(chunk, dict) and chunk.get('type') == 'text':
                    translation_content = chunk.get('text', '')
                elif isinstance(chunk, dict) and chunk.get('type') == 'thinking':
                    thinking_content = chunk.get('thinking', '')
        elif hasattr(thinking_response, 'content'):
            translation_content = thinking_response.content[1]['text']
        else:
            translation_content = str(thinking_response)
            
        # Now create and process plain language version separately using the few-shot prompt with correct language
        target_language = state.get('language', 'English')
        plain_translation_prompt = get_plain_translation_prompt(state['source'], language=target_language)
        
        # Use standard LLM with few-shot prompting for plain translation in target language
        plain_translation_response = llm.invoke(plain_translation_prompt)
        
        # Extract plain translation content
        plain_translation_content = plain_translation_response.content if hasattr(plain_translation_response, 'content') else str(plain_translation_response)
            
        # Get target language from state
        target_language = state.get('language', 'English')
        
        # Use few-shot prompting with regular LLM for structured output extraction
        translation = llm.with_structured_output(Translation_extractor).invoke(
            get_translation_extraction_prompt(state['source'], translation_content, language=target_language)
        )
        
        # Also extract plain translation using few-shot prompting
        plain_translation = llm.with_structured_output(Translation_extractor).invoke(
            get_translation_extraction_prompt(state['source'], plain_translation_content, language=target_language)
        )
        
        # Create feedback entry with both translation and thinking parts
        feedback_entry = f"Iteration {current_iteration} - Initial Translation:\n{translation_content}\n"
        if thinking_content:
            feedback_entry += f"\nTHINKING PROCESS:\n{thinking_content}\n"
            
        return {
            "translation": [translation.extracted_translation],
            "plaintext_translation": plain_translation.extracted_translation,
            "feedback_history": [feedback_entry],
            "iteration": 1
        }


def route_translation(state: State):
    """Route based on both translation quality and formatting."""
    # Only proceed if both content is good AND formatting is correct
    if state["grade"] == "great" and state["formated"]:
        return "Accepted"
    # Max iterations reached but still try to continue with best effort
    elif state["itteration"] >= MAX_TRANSLATION_ITERATIONS:
        return "Accepted"
    else:
        return "Rejected + Feedback"
