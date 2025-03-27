import json
import logging
from tibetan_translator.models import State
from langchain_anthropic import ChatAnthropic
import os
from langchain_core.messages import HumanMessage, SystemMessage

# Import configuration - this will load environment variables from .env
from tibetan_translator.config import LLM_MODEL_NAME, MAX_TOKENS

# Setup logging - file only to avoid interfering with tqdm progress bars
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("translation_debug.log")
        # StreamHandler removed to prevent console output that breaks tqdm
    ]
)
logger = logging.getLogger("tibetan_translator")

# Define few-shot examples for translation extraction
translation_extraction_examples = [
    {"source": "བཅོམ་ལྡན་འདས་རྒྱལ་པོའི་ཁབ་བྱ་རྒོད་ཕུང་པོའི་རི་ལ་དགེ་སློང་གི་དགེ་འདུན་ཆེན་པོ་དང་།",
     "translation": "The Blessed One was residing on Vulture Peak Mountain in Rajagriha with a great assembly of monks."},
    
    {"source": "འདི་སྐད་བདག་གིས་ཐོས་པ་དུས་གཅིག་ན།",
     "translation": "Thus have I heard at one time."},
     
    {"source": "བཅོམ་ལྡན་འདས་མཉན་ཡོད་ན་རྒྱལ་བུ་རྒྱལ་བྱེད་ཀྱི་ཚལ་མགོན་མེད་ཟས་སྦྱིན་གྱི་ཀུན་དགའ་ར་བ་ན།",
     "translation": "The Blessed One was staying in Śrāvastī, in the Jetavana Grove, in the garden of Anāthapiṇḍika."}
]

# Define few-shot examples for plain translation
plain_translation_examples = [
    {
        "source":"དགེ་བ་གཞན་ཀུན་ཆུ་ཤིང་བཞིན་དུ་ནི། །\nའབྲས་བུ་བསྐྱེད་ནས་ཟད་པར་འགྱུར་བ་ཉིད། །\nབྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་། །\nའབྲས་བུ་འབྱིན་པས་མི་ཟད་འཕེལ་བར་འགྱུར། །\n",
        "plaintext_translation":"All other virtuous deeds are like plantain trees—they bear fruit once and then are exhausted. But the tree of the awakening mind is different: it continually produces fruit without ever becoming depleted, and instead grows ever more abundant.\n\nJust as plantain trees wither away after bearing their single harvest, likewise all virtuous actions not embraced by the awakening mind will eventually be consumed after yielding their results. In contrast, the tree of bodhicitta—the mind aspiring to enlightenment for the benefit of all beings—constantly bears fruit that never diminishes. Rather than becoming exhausted, its beneficial results perpetually increase and multiply."
    },
    {
        "source":"སྡིག་པ་ཤིན་ཏུ་མི་བཟད་བྱས་ན་ཡང་། །\nདཔའ་ལ་བརྟེན་ནས་འཇིགས་པ་ཆེན་པོ་ལྟར། །\nགང་ལ་བརྟེན་ནས་ཡུད་ཀྱིས་སྒྲོལ་འགྱུར་བ། །\nདེ་ལ་བག་ཅན་རྣམས་ཀྱིས་ཅིས་མི་བརྟེན། །\n",
        "plaintext_translation":"Even if one has committed the most terrible negative actions,Like a person who gains protection from great dangers by relying on a brave protector,By relying on bodhicitta, one can be swiftly liberated in an instant.So why would conscientious people not rely on this?"
    }
]

# Define few-shot examples for combined commentary
combined_commentary_examples = [
    {
        "source":"དགེ་བ་གཞན་ཀུན་ཆུ་ཤིང་བཞིན་དུ་ནི། །\nའབྲས་བུ་བསྐྱེད་ནས་ཟད་པར་འགྱུར་བ་ཉིད། །\nབྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་། །\nའབྲས་བུ་འབྱིན་པས་མི་ཟད་འཕེལ་བར་འགྱུར། །\n",
        "combined_commentary":"དགེ་བ་གཞན་ཀུན་ཆུ་ཤིང་བཞིན་དུ་ནི། །\n(All other virtuous actions are like plantain trees)\n\nThis verse compares all virtuous actions not embraced by bodhicitta to plantain (or banana) trees. Just as the trunk of a plantain tree bears fruit only once and then becomes exhausted, similarly all other kinds of merit not embraced by bodhicitta will eventually be depleted after ripening. These virtuous actions that accord with ordinary merit will produce temporary fruits such as higher rebirth but then become exhausted.\n\nའབྲས་བུ་བསྐྱེད་ནས་ཟད་པར་འགྱུར་བ་ཉིད། །\n(After bearing fruit, they become exhausted)\n\nAfter producing their results, these ordinary virtuous actions are depleted, just as the plantain tree dies after bearing fruit. Even the spiritual accomplishments of Śrāvakas and Pratyekabuddhas ultimately reach a state where their aggregates become extinguished without remainder, as they lack the inexhaustible quality that bodhicitta provides.\n\nབྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་། །\n(But the tree of bodhicitta constantly)\n\nIn contrast, virtuous actions embraced by bodhicitta are compared to excellent wish-fulfilling trees. The Precious Casket Sūtra explains: \"Mañjuśrī, it is like this: various trees grow and flourish when sustained by the four elements. Likewise, when the roots of virtue are embraced by the mind of enlightenment and dedicated to omniscience, they flourish and increase.\"\n\nའབྲས་བུ་འབྱིན་པས་མི་ཟད་འཕེལ་བར་འགྱུར། །\n(Produces fruit without exhaustion and continues to increase)\n\nThe tree of bodhicitta constantly and continuously yields the ripened fruit of temporary excellent happiness for gods and humans, which is never exhausted. The fruit increases progressively and ultimately produces the vast results counted among the merit accumulations of the Buddha's form body. As stated in the Akṣayamati-nirdeśa Sūtra: \"Just as water droplets that fall into the great ocean are not exhausted until the end of the kalpa, likewise virtuous deeds dedicated to enlightenment are not exhausted until the attainment of the essence of enlightenment.\" This is the fourth point illustrating the benefits of bodhicitta."
    },
    {
        "source":"སྡིག་པ་ཤིན་ཏུ་མི་བཟད་བྱས་ན་ཡང་། །\nདཔའ་ལ་བརྟེན་ནས་འཇིགས་པ་ཆེན་པོ་ལྟར། །\nགང་ལ་བརྟེན་ནས་ཡུད་ཀྱིས་སྒྲོལ་འགྱུར་བ། །\nདེ་ལ་བག་ཅན་རྣམས་ཀྱིས་ཅིས་མི་བརྟེན། །\n",
        "combined_commentary":"སྡིག་པ་ཤིན་ཏུ་མི་བཟད་བྱས་ན་ཡང་། །\nEven if one has committed extremely unbearable negative actions such as abandoning the Dharma, harming the Three Jewels, or committing the five heinous acts that would certainly lead to experiencing the sufferings of the Avīci hell,\n\nདཔའ་ལ་བརྟེན་ནས་འཇིགས་པ་ཆེན་པོ་ལྟར། །\njust as a criminal who has committed terrible deeds might be protected from great dangers by relying on a brave escort or hero (like a person who has killed someone's father seeking protection from a powerful person against the vengeful son),\n\nགང་ལ་བརྟེན་ནས་ཡུད་ཀྱིས་སྒྲོལ་འགྱུར་བ། །\nsimilarly, by relying on the precious bodhicitta, one will be swiftly liberated in an instant from the ripening effects of those great negative actions—the sufferings of lower rebirths and hell realms,\n\nདེ་ལ་བག་ཅན་རྣམས་ཀྱིས་ཅིས་མི་བརྟེན། །\nso why would those who are conscientious about observing what should be adopted and rejected, and who fear negative actions, not rely on this bodhicitta? As stated in the Teaching of Inexhaustible Intelligence (Akṣayamatinirdeśa): \"Son of noble family, it is like this: One who relies on a brave person is not afraid of any enemies. Similarly, a bodhisattva who properly relies on the brave person who has generated bodhicitta is not afraid of any enemies of wrongdoing.\" This is the fifth point, illustrating how bodhicitta, like fire, destroys sin from its root."
    }
]

def get_translation_extraction_prompt(source_text, llm_response):
    """Generate a few-shot prompt for translation extraction."""
    system_message = SystemMessage(content="""You are an expert assistant specializing in extracting translations from text. Your task is to:

1. Identify the actual translation portion of the text
2. Extract ONLY the translation, not any translator's notes, explanations, or formatting instructions
3. Preserve the exact formatting of the translation including line breaks
4. Remove any metadata, headers, or annotations that are not part of the translation itself

DO NOT include any explanatory text or commentary in your extraction. Return ONLY the translation text.""")
    
    # Create few-shot examples as a conversation
    messages = [system_message]
    
    # Add few-shot examples
    for example in translation_extraction_examples:
        # Add user message with request
        messages.append(HumanMessage(content=f"""Extract the translation from the following text:

SOURCE TEXT:
{example['source']}

LLM RESPONSE:
This is a translation of the Tibetan text above. The Tibetan says: {example['source']}

Translation:
{example['translation']}
Note: This translation preserves the meaning while making it accessible in natural English. The term "Bhagavan" refers to the Buddha...
"""))
        
        # Add assistant's correct response as an AI message
        messages.append({"type": "ai", "content": example['translation']})
    
    # Add the actual request
    messages.append(HumanMessage(content=f"""Extract the translation from the following text:

SOURCE TEXT:
{source_text}

LLM RESPONSE:
{llm_response}

Return ONLY the translation portion, no explanatory text or metadata."""))
    
    return messages

def get_plain_translation_prompt(source_text, language="English"):
    """Generate a few-shot prompt for plain language translation using a multi-turn conversation format."""
    system_message = SystemMessage(content=f"""You are an expert translator of Tibetan Buddhist texts into clear, accessible modern {language}. Your task is to:

1. Create a plain, accessible translation that preserves the meaning but uses simple, straightforward {language}
2. Focus on clarity and readability for modern readers without specialized Buddhist knowledge
3. Make the translation direct and concise while maintaining all key content
4. Use natural, flowing language that would be understood by educated non-specialists

LANGUAGE-SPECIFIC REQUIREMENTS FOR {language.upper()}:
- Your translation MUST be in fluent, natural {language} as spoken by native speakers
- Use appropriate {language} grammar, syntax, and idiomatic expressions
- Maintain proper {language} sentence structure and flow
- Choose words and phrases that sound natural in {language}
- Avoid awkward phrasing, word-for-word translations, or unnatural constructions

Your translation should be accurate but prioritize clarity, naturalness, and accessibility over technical precision.
IMPORTANT: Your translation MUST be in {language} and must sound natural to native {language} speakers.""")
    
    # Start the conversation with the system message
    messages = [system_message]
    
    # Add few-shot examples as a multi-turn conversation
    for example in plain_translation_examples:
        # Human message
        messages.append(HumanMessage(content=f"""Translate this Tibetan Buddhist text into plain, accessible modern {language}:

{example['source']}"""))
        
        # Assistant message (not SystemMessage) with the expected response
        messages.append({"type": "ai", "content": example['plaintext_translation']})
    
    # Add the actual request
    messages.append(HumanMessage(content=f"""Translate this Tibetan Buddhist text into plain, accessible modern {language}:

{source_text}"""))
    
    return messages


def get_zero_shot_commentary_prompt(source_text, language="English"):
    """Generate a zero-shot prompt for creating commentary when no existing commentaries are available."""
    system_message = SystemMessage(content=f"""You are an expert in Tibetan Buddhist philosophy tasked with creating a commentary on Tibetan Buddhist texts. You must write a commentary in {language}. Your task is to:

1. Analyze the source text carefully, line by line
2. Explain the doctrinal significance of each line or phrase
3. Provide context on any Buddhist concepts mentioned
4. Elucidate philosophical implications
5. Clarify technical terminology
6. Consider different interpretative traditions where relevant

Your commentary should be scholarly yet accessible, balancing philological detail with philosophical insight.
IMPORTANT: Your commentary MUST be written in {language}.""")
    
    # For zero-shot, we just create a direct request
    messages = [system_message]
    
    # Add the request
    messages.append(HumanMessage(content=f"""Create a detailed commentary for this Tibetan Buddhist text:

SOURCE TEXT:
{source_text}

Please analyze this text line by line, explaining its meaning, philosophical context, and doctrinal significance in {language}.
"""))
    
    return messages

def create_source_analysis(source_text, sanskrit_text="", language="English"):
    """Create a focused analysis of the source text without speculative commentary."""
    
    # Create prompt for source-focused analysis
    system_message = SystemMessage(content=f"""Analyze this Tibetan Buddhist text directly from the source without speculative commentary. Your task is to:

1. Identify grammatical structures and linguistic patterns in the Tibetan text
2. Note any technical Buddhist terminology and its precise meaning
3. Document structural elements (verse format, paragraph breaks, etc.)
4. Highlight key concepts but avoid interpretive speculation
5. Provide literal meanings while noting potential ambiguities

Focus ONLY on what can be directly determined from the text itself.
IMPORTANT: Your analysis MUST be written in {language}.""")
    
    # Create content with conditional Sanskrit part
    content = f"""Analyze this Tibetan Buddhist text:

SOURCE TEXT:
{source_text}

"""
    # Add Sanskrit text if available
    if sanskrit_text:
        content += f"SANSKRIT TEXT (if available):\n{sanskrit_text}\n\n"
    
    content += f"Please provide a detailed linguistic and structural analysis in {language}, focusing exclusively on the text itself without speculative interpretation."
    
    messages = [system_message, HumanMessage(content=content)]
    
    # Use thinking LLM for careful analysis
    response = llm_thinking.invoke(messages)
    
    # Extract content from thinking response
    analysis_content = ""
    
    if isinstance(response, list):
        # Handle thinking output format, extracting only the text part
        for chunk in response:
            if isinstance(chunk, dict) and chunk.get('type') == 'text':
                analysis_content = chunk.get('text', '')
    elif hasattr(response, 'content'):
        if isinstance(response.content, list) and len(response.content) > 1:
            # Extract text from the second element (typical thinking response structure)
            analysis_content = response.content[1].get('text', '')
        else:
            analysis_content = response.content
    else:
        analysis_content = str(response)
    
    return analysis_content

def get_enhanced_translation_prompt(sanskrit, source, source_analysis, language="English"):
    """Generate an enhanced prompt for fluent yet accurate translation."""
    return f"""
    Translate this Tibetan Buddhist text into natural, eloquent {language}:

    Sanskrit text:
    {sanskrit}

    Source Text:
    {source}

    Source Analysis:
    {source_analysis}

    TRANSLATION PRIORITIES:
    1. FLUENCY: Create text that flows naturally in {language} as if originally composed in it
    2. ACCURACY: Preserve the precise meaning of every term and concept
    3. STRUCTURE: Maintain the original's structural elements while adapting to {language} literary norms
    4. TERMINOLOGY: Use established Buddhist terminology in {language} where it exists

    LANGUAGE-SPECIFIC GUIDANCE FOR {language.upper()}:
    - Restructure sentences to match natural {language} rhythm and flow
    - Use idiomatic expressions native to {language} literary tradition
    - Adapt sentence length and complexity to {language} conventions
    - Choose terminology that resonates with {language}-speaking Buddhist practitioners
    - Balance technical precision with literary elegance

    HANDLING CHALLENGING ELEMENTS:
    - For ambiguous passages: provide the most natural reading but stay close to literal meaning
    - For technical terms: use established translations if they exist, otherwise translate conceptually
    - For cultural references: preserve the original concept while making it accessible to {language} readers
    - For poetic elements: capture the aesthetic quality in {language} poetic conventions
    
    AVOID:
    - Word-for-word translation that creates awkward {language} phrasing
    - Overly simplifying complex concepts
    - Adding interpretive content not present in the source
    - Losing structural elements (verse format, sections, etc.)
    - Using inconsistent terminology for repeated concepts

    YOUR GOAL: A translation that a native {language} speaker with Buddhist knowledge would recognize as both authentic to the tradition and natural in their language.

    Generate only the translation with no explanatory notes.
    """

def get_combined_commentary_prompt(source_text, commentaries, has_commentaries=True, language="English"):
    """Generate a prompt for creating combined commentary, with fallback for cases with no commentaries."""
    # If there are no commentaries, use zero-shot mode instead
    if not has_commentaries:
        return get_zero_shot_commentary_prompt(source_text, language)
    
    system_message = SystemMessage(content=f"""You are an expert in Tibetan Buddhist philosophy tasked with creating a comprehensive, integrated commentary on Tibetan Buddhist texts. Your task is to:

1. Analyze multiple commentaries on the same text and integrate them into a single cohesive explanation
2. Preserve all key philosophical points from each commentary
3. Explain each line of the source text in detail, including its doctrinal significance
4. Connect the commentaries in a way that builds a clearer understanding of the text
5. Ensure all technical Buddhist terminology is properly explained
6. Combined Commentary shouldnt have the tittle # Combined Commentary in {language}.

Your combined commentary should be thorough, scholarly, and provide a complete analysis of the text.
IMPORTANT: Your commentary MUST be written in {language}.""")
    
    # Create few-shot examples as a conversation
    messages = [system_message]
    
    # Add few-shot examples
    for example in combined_commentary_examples:
        # Add user message with request
        messages.append(HumanMessage(content=f"""Create a combined commentary for this Tibetan Buddhist text based on multiple source commentaries:

SOURCE TEXT:
{example['source']}

COMMENTARIES:
[Multiple commentaries would be provided here...]
"""))
        
        # Add assistant's correct response as an AI message
        messages.append({"type": "ai", "content": example['combined_commentary']})
    
    # Add the actual request
    messages.append(HumanMessage(content=f"""Create a combined commentary for this Tibetan Buddhist text based on multiple source commentaries:

IMPORTANT: Your commentary MUST be written in {language}.

SOURCE TEXT:
{source_text}

COMMENTARIES:
{commentaries}
"""))
    
    return messages


# Initialize standard LLM instance 
llm = ChatAnthropic(model=LLM_MODEL_NAME, max_tokens=MAX_TOKENS)

# Initialize LLM instance with thinking capability for complex reasoning tasks
llm_thinking = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    max_tokens=5000,
    thinking={"type": "enabled", "budget_tokens": 2000},
)

def dict_to_text(d, indent=0):
    """Convert dictionary to formatted text."""
    text = ""
    spacing = " " * indent
    
    for key, value in d.items():
        if isinstance(value, dict):
            text += f"{spacing}{key}:\n{dict_to_text(value, indent + 2)}"
        else:
            text += f"{spacing}{key}: {value}\n"
    
    return text

def convert_state_to_jsonl(state_dict: State, file_path: str):
    """Save the state dictionary in JSONL format."""
    with open(file_path, 'a', encoding='utf-8') as f:
        json.dump(state_dict, f, ensure_ascii=False)
        f.write("\n")
def get_json_data(file_path='commentary_1.json'):
    """Load data from a JSON file."""
    logger.debug(f"Loading JSON from file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            file_content = json_file.read()
            logger.debug(f"Raw file content: {file_content[:200]}...")  # Log first 200 chars
            
            # Log type information before parsing
            logger.debug(f"File content type: {type(file_content)}")
            
            try:
                data = json.loads(file_content)
                logger.debug(f"Parsed data type: {type(data)}")
                
                # If data contains entries, log their structure
                if 'entries' in data:
                    logger.debug(f"Entries type: {type(data['entries'])}")
                    logger.debug(f"First entry sample: {str(data['entries'][0]) if data['entries'] and isinstance(data['entries'], list) else 'No entries or not a list'}")
                
                return data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Error position: {e.pos}, line: {e.lineno}, column: {e.colno}")
                logger.error(f"Document snippet at error: {file_content[max(0, e.pos-50):e.pos+50]}")
                raise
    except Exception as e:
        logger.error(f"Error loading JSON file: {str(e)}")
        raise
