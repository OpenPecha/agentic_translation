from langgraph.graph import StateGraph, START, END
from tibetan_translator.models import State
from tibetan_translator.processors.commentary import (
    commentary_translator_1, commentary_translator_2, commentary_translator_3, aggregator
)
from tibetan_translator.processors.translation import translation_generator, route_translation
from tibetan_translator.processors.evaluation import llm_call_evaluator
# We no longer need these functions since formatting is now integrated into the main evaluator
# from tibetan_translator.processors.evaluation import route_structured
# from tibetan_translator.processors.formatting import formater, format_evaluator_feedback
from tibetan_translator.processors.glossary import generate_glossary

# Initialize the workflow graph
optimizer_builder = StateGraph(State)

# Add processing nodes
optimizer_builder.add_node("commentary_translator_1", commentary_translator_1)
optimizer_builder.add_node("commentary_translator_2", commentary_translator_2)
optimizer_builder.add_node("commentary_translator_3", commentary_translator_3)
optimizer_builder.add_node("aggregator", aggregator)
optimizer_builder.add_node("translation_generator", translation_generator)
optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)
optimizer_builder.add_node("generate_glossary", generate_glossary)
# These nodes are no longer needed as formatting is now part of the main evaluator
# optimizer_builder.add_node("format_evaluator_feedback", format_evaluator_feedback)
# optimizer_builder.add_node("formater", formater)

# Define workflow edges
optimizer_builder.add_edge(START, "commentary_translator_1")
optimizer_builder.add_edge(START, "commentary_translator_2")
optimizer_builder.add_edge(START, "commentary_translator_3")
optimizer_builder.add_edge("commentary_translator_1", "aggregator")
optimizer_builder.add_edge("commentary_translator_2", "aggregator")
optimizer_builder.add_edge("commentary_translator_3", "aggregator")
optimizer_builder.add_edge("aggregator", "translation_generator")
optimizer_builder.add_edge("translation_generator", "llm_call_evaluator")

optimizer_builder.add_conditional_edges(
    "llm_call_evaluator",
    route_translation,
    {
        "Accepted": "generate_glossary",  # Now goes directly to glossary generation
        "Rejected + Feedback": "translation_generator"
    }
)

# No longer need these edges since formatting evaluation is integrated
# optimizer_builder.add_conditional_edges(
#     "format_evaluator_feedback",
#     route_structured,
#     {
#         "Accepted": "generate_glossary",
#         "Rejected + Feedback": "formater"
#     }
# )
# optimizer_builder.add_edge("formater", "format_evaluator_feedback")

optimizer_builder.add_edge("generate_glossary", END)

# Compile the workflow
optimizer_workflow = optimizer_builder.compile()