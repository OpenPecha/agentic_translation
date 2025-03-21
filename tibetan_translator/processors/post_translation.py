import json
import logging
import sys
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from tqdm import tqdm
from pydantic import BaseModel, Field

from tibetan_translator.models import State, GlossaryEntry
from tibetan_translator.utils import llm
from tibetan_translator.config import LLM_MODEL_NAME, MAX_TOKENS

# Set up dual logging: console for progress, file for details
def setup_logging():
    # Create logger
    logger = logging.getLogger("post_translation")
    logger.setLevel(logging.DEBUG)
    
    # Create console handler with higher threshold for clean progress display
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s')  # Simple format for console
    console.setFormatter(console_format)
    
    # Create file handler with detailed logging
    file_handler = logging.FileHandler("post_translation_debug.log")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console)
    logger.addHandler(file_handler)
    logger.propagate = False  # Prevent duplicate logs
    
    return logger

logger = setup_logging()

# Pydantic models for structured output
class WordStandardization(BaseModel):
    standard_translation: str = Field(
        description="The standard translation of the word",
    )
    tibetan_term: str = Field(
        description="The tibetan term to be standardized",
    )
    rationale: str = Field(
        description="The rationale for the standardization",
    )
    target_audience: str = Field(
        description="Ranked target audience for the standardization, separated by commas",
    )

class PostTranslation(BaseModel):
    standardised_translation: str = Field(
        description="The standardised translation of the source text",
    )

class WordByWordTranslation(BaseModel):
    word_by_word_translation: str = Field(
        description="The word by word translation of the source text",
    )

def analyze_term_frequencies(glossaries: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Analyze term frequencies across all glossaries to identify terms with multiple translations.
    
    Args:
        glossaries: List of glossary entries from all documents
        
    Returns:
        DataFrame with tibetan_term and translation_freq columns
    """
    logger.info("📊 Analyzing term frequencies across corpus...")
    logger.debug(f"Processing {len(glossaries)} glossary entries")
    
    # Initialize data structures
    term_translations = {}
    
    # Process with progress tracking
    for glossary in tqdm(glossaries, desc="Analyzing term frequencies"):
        for entry in glossary:
            tibetan_term = entry.get('tibetan_term', '')
            translation = entry.get('translation', '')
            
            if not tibetan_term or not translation:
                continue
                
            # Add to term_translations dict
            if tibetan_term not in term_translations:
                term_translations[tibetan_term] = {}
                
            if translation not in term_translations[tibetan_term]:
                term_translations[tibetan_term][translation] = 0
                
            term_translations[tibetan_term][translation] += 1
    
    # Convert to DataFrame format
    data = []
    for term, translations in term_translations.items():
        # Format as semicolon-separated string with frequencies
        translation_freq = ";".join([
            f"{trans} ({freq})" 
            for trans, freq in sorted(translations.items(), key=lambda x: x[1], reverse=True)
        ])
        
        data.append({
            'tibetan_term': term,
            'translation_freq': translation_freq,
            'translation_count': len(translations)
        })
    
    result_df = pd.DataFrame(data)
    logger.info(f"✅ Term frequency analysis complete: found {len(data)} unique terms")
    logger.info(f"  - {len(result_df[result_df['translation_count'] > 1])} terms have multiple translations")
    
    return result_df

def generate_standardization_examples(glossary: pd.DataFrame, corpus: List[Dict[str, Any]], 
                              max_samples_per_term: int = 10, language: str = 'English') -> List[str]:
    """
    Generate standardization examples for terms with multiple translations.
    
    Args:
        glossary: DataFrame with tibetan_term and translation_freq columns
        corpus: List of document dictionaries with source, translation, and sanskrit
        max_samples_per_term: Maximum number of examples to include per term
        language: Target language for standardized terms (default: English)
        
    Returns:
        List of standardization example strings
    """
    logger.info("📝 Generating standardization examples...")
    examples = []
    multi_translation_terms = glossary[glossary['translation_count'] > 1]
    
    logger.debug(f"Generating examples for {len(multi_translation_terms)} terms with multiple translations")
    
    # Create translation file for lookup
    translation_file = pd.DataFrame([
        {'source': doc.get('source', ''), 
         'translation': doc.get('translation', ''),
         'sanskrit': doc.get('sanskrit', '')} 
        for doc in corpus
    ])
    
    # Ensure no NaN values in 'source' column
    translation_file['source'] = translation_file['source'].fillna("")
    
    # Process each term with multiple translations
    for i in tqdm(range(len(multi_translation_terms)), desc="Generating examples"):
        term_row = multi_translation_terms.iloc[i]
        
        # Get the Tibetan term
        tibetan_term = term_row['tibetan_term']
        
        # Find samples containing this term
        term_mask = translation_file['source'].str.contains(tibetan_term, na=False)
        samples = translation_file[term_mask][['source', 'translation', 'sanskrit']]
        
        # Limit to max_samples_per_term
        samples = samples.head(max_samples_per_term)
        
        # Only proceed if we found examples
        if len(samples) > 0 :
            # Build the example text
            example = f"Usage examples:\n\n"
            
            # Add each sample
            for _, sample in samples.iterrows():
                example += f"Sanskrit: {sample['sanskrit']}\n"
                example += f"Source: {sample['source']}\n"
                example += f"Translation: {sample['translation']}\n\n"
            
            # Add the Tibetan term and translation candidates
            example += f"Tibetan Term: {tibetan_term} Translation: {term_row['translation_freq'].replace(';', ',')}\n\n"
            
            # Add the standardization protocol
            example += f"""Translation Standardization Protocol for {language}:

1. Context Compatibility Analysis: Evaluate each candidate translation by substituting it across all attested examples to ensure semantic congruence in every context.

2. Canonical Alignment: When parallel Sanskrit attestations exist, prioritize translations that maintain terminological correspondence with the Sanskrit source tradition while remaining comprehensible in {language}.

3. Hierarchical Selection Criteria:
   a. Cross-contextual applicability (primary determinant)
   b. Terminological ecosystem coherence (relationship to established glossary terms)
   c. Register appropriateness for target audience in {language}
   d. Naturalness and fluidity in {language}

4. Validation Through Bidirectional Testing: Verify that the standardized term maps consistently back to the Tibetan term without ambiguity or semantic drift.

IMPORTANT: Your standardized translation MUST be in {language}, not English (unless the target language is English).

Output:
Tibetan Term: [Tibetan term]
Selected standard translation: [Selected translation in {language}]
Rationale: [Brief explanation of why this translation was selected based on the rules]
Target audience: [Target audience in order of priority]"""
            
            examples.append(example)
    
    logger.info(f"✅ Generated {len(examples)} standardization examples")
    return examples

def standardize_terminology(examples: List[str], language: str = 'English') -> List[Dict[str, str]]:
    """
    Standardize terminology by selecting the best translation for each term.
    
    Args:
        examples: List of standardization example strings
        language: Target language for standardized terms (default: English)
        
    Returns:
        List of dictionaries with standardized term data
    """
    logger.info(f"🔄 Standardizing terminology for {language}...")
    
    # Create LLM with structured output
    word_standardizer = llm.with_structured_output(WordStandardization)
    
    # Process in batches with progress reporting
    standardized_words = []
    batch_size = 30
    batches = [examples[i:i + batch_size] for i in range(0, len(examples), batch_size)]
    
    for batch_idx, batch in enumerate(tqdm(batches, desc="Standardizing terms")):
        try:
            logger.info(f"🔄 Batch {batch_idx+1}/{len(batches)}: Processing {len(batch)} terms")
            
            # Process the batch
            results = word_standardizer.batch(batch)
            
            # Process results and validate language
            for result in results:
                result_dict = dict(result)
                
                # Log the standardized translation
                logger.debug(f"Standardized term: {result_dict.get('tibetan_term', '')} → {result_dict.get('standard_translation', '')}")
                
                # Add language info if not present in the rationale
                if language != 'English' and 'rationale' in result_dict:
                    if not f"in {language}" in result_dict['rationale']:
                        result_dict['rationale'] += f" This translation is optimal for {language} speakers."
                
                standardized_words.append(result_dict)
                
            logger.debug(f"Successfully processed batch {batch_idx+1}")
            
        except Exception as e:
            logger.error(f"❌ Error in batch {batch_idx+1}: {str(e)}")
            logger.info(f"🔄 Retrying batch {batch_idx+1}...")
            
            try:
                # Retry once
                results = word_standardizer.batch(batch)
                
                # Process results and validate language
                for result in results:
                    result_dict = dict(result)
                    
                    # Log the standardized translation
                    logger.debug(f"Standardized term on retry: {result_dict.get('tibetan_term', '')} → {result_dict.get('standard_translation', '')}")
                    
                    # Add language info if not present in the rationale
                    if language != 'English' and 'rationale' in result_dict:
                        if not f"in {language}" in result_dict['rationale']:
                            result_dict['rationale'] += f" This translation is optimal for {language} speakers."
                    
                    standardized_words.append(result_dict)
                
                logger.debug(f"Successfully processed batch {batch_idx+1} on retry")
            except Exception as retry_e:
                logger.error(f"❌ Error on retry for batch {batch_idx+1}: {str(retry_e)}")
                logger.info(f"⚠️ Processing items individually for batch {batch_idx+1}")
                
                # Process each item individually
                for item_idx, item in enumerate(batch):
                    try:
                        result = word_standardizer.invoke(item)
                        result_dict = dict(result)
                        
                        # Log the standardized translation
                        logger.debug(f"Standardized term individually: {result_dict.get('tibetan_term', '')} → {result_dict.get('standard_translation', '')}")
                        
                        # Add language info if not present in the rationale
                        if language != 'English' and 'rationale' in result_dict:
                            if not f"in {language}" in result_dict['rationale']:
                                result_dict['rationale'] += f" This translation is optimal for {language} speakers."
                        
                        standardized_words.append(result_dict)
                        logger.debug(f"Successfully processed item {item_idx+1} individually")
                    except Exception as item_e:
                        logger.error(f"❌ Failed to process item {item_idx+1}: {str(item_e)}")
    
    logger.info(f"✅ Standardized {len(standardized_words)} terms")
    return standardized_words

def apply_standardized_terms(corpus: List[Dict[str, Any]], standardized_glossary: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Apply standardized terminology to all translations in the corpus.
    
    Args:
        corpus: List of document dictionaries
        standardized_glossary: DataFrame with standardized terms
        
    Returns:
        Updated corpus with standardized translations
    """
    logger.info("📝 Applying standardized terminology to translations...")
    
    # Create LLM with structured output
    post_translator = llm.with_structured_output(PostTranslation)
    
    # Find documents with standardizable terms
    documents_to_process = []
    prompts = []
    doc_indices = []
    
    for doc_idx, doc in enumerate(tqdm(corpus, desc="Analyzing documents")):
        # Extract Tibetan terms in document
        source_text = doc.get('source', '')
        tibetan_terms = []
        
        for term in standardized_glossary['tibetan_term']:
            if term in source_text:
                tibetan_terms.append(term)
        
        # Only process documents with standardizable terms
        if tibetan_terms:
            documents_to_process.append(doc)
            doc_indices.append(doc_idx)
            
            # Build glossary for this document
            doc_glossary = []
            for term in tibetan_terms:
                term_row = standardized_glossary[standardized_glossary['tibetan_term'] == term].iloc[0]
                doc_glossary.append({
                    'tibetan_term': term,
                    'standard_translation': term_row['standard_translation']
                })
            
            # Format glossary as text
            glossary_text = ""
            for entry in doc_glossary:
                for key, value in entry.items():
                    glossary_text += f"{key}:-{value}\n"
            
            # Get translation - handle string, list, and JSON string cases
            raw_translation = doc.get('translation', '')
            
            # If translation is a list, use the last translation (most recent/final version)
            if isinstance(raw_translation, list) and raw_translation:
                logger.debug(f"Translation is a list with {len(raw_translation)} options")
                
                # Use the last translation in the list
                last_translation = raw_translation[-1] if raw_translation else ""
                logger.debug(f"Using last translation (item {len(raw_translation)}) of length {len(last_translation)}")
                
                # Store all translations as plaintext_translation if not already present
                if 'plaintext_translation' not in doc:
                    doc['plaintext_translation'] = raw_translation
                
                raw_translation = last_translation
            
            # If translation is a string but might be a JSON string (containing a list or object)
            elif isinstance(raw_translation, str) and (
                (raw_translation.startswith('[') and raw_translation.endswith(']')) or
                (raw_translation.startswith('{') and raw_translation.endswith('}'))
            ):
                logger.debug(f"Translation appears to be a JSON string, attempting to parse")
                try:
                    # Try to parse as JSON
                    parsed_translation = json.loads(raw_translation)
                    
                    # Handle parsed result based on type
                    if isinstance(parsed_translation, list) and parsed_translation:
                        # If it's a list, use the last item
                        if 'plaintext_translation' not in doc:
                            doc['plaintext_translation'] = parsed_translation
                        
                        raw_translation = parsed_translation[-1]
                        logger.debug(f"Successfully parsed JSON string to list, using last item")
                    
                    elif isinstance(parsed_translation, dict) and 'translation' in parsed_translation:
                        # If it's an object with a translation field, use that
                        raw_translation = parsed_translation['translation']
                        logger.debug(f"Successfully parsed JSON string to object, using translation field")
                    
                    else:
                        # Otherwise just convert to string
                        raw_translation = str(parsed_translation)
                        logger.debug(f"Parsed JSON but using string representation")
                
                except json.JSONDecodeError as e:
                    # If parsing fails, keep as string
                    logger.debug(f"Failed to parse as JSON, using as plain string: {str(e)}")
            
            # Create prompt for standardization
            prompt = f"""
Standardize the following translation by ONLY replacing non-standard terminology with the approved equivalents from the glossary. Ensure the resulting text remains natural and accurate.

SOURCE TEXT:
{doc.get('source', '')}

RAW TRANSLATION:
{raw_translation}

STANDARDIZED GLOSSARY:
{glossary_text}

COMMENTARY (for context only):
{doc.get('combined_commentary', '')}

INSTRUCTIONS:
1. Identify terms in the raw translation that have standardized equivalents in the glossary
2. Replace ONLY those specific terms with their standardized versions
3. Make minimal adjustments if necessary to maintain grammatical correctness
4. Do not change any other aspects of the translation
5. Ensure the final text reads naturally and preserves the original meaning and format

STANDARDIZED TRANSLATION:
[Provide standardized translation here]
"""
            prompts.append(prompt)
    
    logger.info(f"Found {len(documents_to_process)} documents with standardizable terms")
    
    # Process prompts in batches
    standardized_translations = [None] * len(prompts)
    batch_size = 10
    batches = [prompts[i:i + batch_size] for i in range(0, len(prompts), batch_size)]
    batch_indices = [list(range(i, min(i + batch_size, len(prompts)))) for i in range(0, len(prompts), batch_size)]
    
    for batch_idx, (batch, indices) in enumerate(zip(batches, batch_indices)):
        try:
            logger.info(f"🔄 Batch {batch_idx+1}/{len(batches)}: Processing {len(batch)} documents")
            
            # Process the batch
            results = post_translator.batch(batch)
            
            # Store results
            for i, result in zip(indices, results):
                standardized_translations[i] = result.standardised_translation
                
        except Exception as e:
            logger.error(f"❌ Error in batch {batch_idx+1}: {str(e)}")
            logger.info(f"🔄 Retrying batch {batch_idx+1}...")
            
            try:
                # Retry once
                results = post_translator.batch(batch)
                for i, result in zip(indices, results):
                    standardized_translations[i] = result.standardised_translation
            except Exception as retry_e:
                logger.error(f"❌ Error on retry for batch {batch_idx+1}: {str(retry_e)}")
                
                # Process each item individually
                for idx, (i, prompt) in enumerate(zip(indices, batch)):
                    try:
                        result = post_translator.invoke(prompt)
                        standardized_translations[i] = result.standardised_translation
                        logger.debug(f"Successfully processed item {idx+1} individually")
                    except Exception as item_e:
                        logger.error(f"❌ Failed to process item {idx+1}: {str(item_e)}")
                        standardized_translations[i] = documents_to_process[i].get('translation', '')  # Fall back to original
    
    # Update corpus with standardized translations
    updated_corpus = corpus.copy()
    for i, doc_idx in enumerate(doc_indices):
        if standardized_translations[i]:
            # Store original translation as plaintext_translation if not already present
            if 'plaintext_translation' not in updated_corpus[doc_idx]:
                updated_corpus[doc_idx]['plaintext_translation'] = updated_corpus[doc_idx].get('translation', '')
            
            # Update with standardized translation
            updated_corpus[doc_idx]['translation'] = standardized_translations[i]
            
            # Ensure required fields are present
            for field in ['source', 'combined_commentary']:
                if field not in updated_corpus[doc_idx]:
                    logger.warning(f"⚠️ Missing required field '{field}' in document {doc_idx+1}")
                    updated_corpus[doc_idx][field] = ""
    
    logger.info(f"✅ Applied standardized terminology to {len(documents_to_process)} documents")
    return updated_corpus

def generate_word_by_word(corpus: List[Dict[str, Any]], language: str = 'English') -> List[Dict[str, Any]]:
    """
    Generate word-by-word translations for all documents in the corpus.
    
    Args:
        corpus: List of document dictionaries with source and translation
        language: Target language for translations (default: English)
        
    Returns:
        Updated corpus with word-by-word translations
    """
    logger.info("🔤 Generating word-by-word mappings...")
    
    # Create LLM with structured output
    word_by_word_translator = llm.with_structured_output(WordByWordTranslation)
    
    # Create prompts
    prompts = []
    for doc in tqdm(corpus, desc="Preparing word-by-word prompts"):
        # Handle translation that might be a list or JSON string
        translation = doc.get('translation', '')
        
        # If translation is a list, use the last item
        if isinstance(translation, list) and translation:
            # Use the last translation in the list (most recent/final version)
            translation = translation[-1] if translation else ""
            logger.debug(f"Using last translation (item {len(doc['translation'])}) from list for word-by-word mapping")
        
        # If translation is a JSON string, try to parse it
        elif isinstance(translation, str) and (
            (translation.startswith('[') and translation.endswith(']')) or
            (translation.startswith('{') and translation.endswith('}'))
        ):
            logger.debug(f"Translation appears to be a JSON string, attempting to parse for word-by-word mapping")
            try:
                # Try to parse as JSON
                parsed_translation = json.loads(translation)
                
                # Handle parsed result based on type
                if isinstance(parsed_translation, list) and parsed_translation:
                    # If it's a list, use the last item
                    translation = parsed_translation[-1]
                    logger.debug(f"Parsed JSON string to list, using last item for word-by-word mapping")
                
                elif isinstance(parsed_translation, dict) and 'translation' in parsed_translation:
                    # If it's an object with a translation field, use that
                    translation = parsed_translation['translation']
                    logger.debug(f"Parsed JSON string to object, using translation field for word-by-word mapping")
                
                else:
                    # Otherwise just convert to string
                    translation = str(parsed_translation)
                    logger.debug(f"Parsed JSON but using string representation for word-by-word mapping")
            
            except json.JSONDecodeError as e:
                # If parsing fails, keep as string
                logger.debug(f"Failed to parse as JSON, using as plain string: {str(e)}")
        
        prompt = f"""
Given source text and translation, create a word-by-word translation based on the standardized translation. Ensure the word-by-word translation accurately reflects the meaning of the standardized translation.

Source Text:
{doc.get('source', '')}

Standardized Translation:
{translation}

Target Language: {language}

WORD-BY-WORD TRANSLATION:
Format: [Tibetan word/phrase] → [{language} translation]

IMPORTANT: Your translations MUST be in {language}, not English (unless {language} is English).

Example for {language}:
བྱང་ཆུབ་སེམས་དཔའ་ → {"菩萨" if language == "Chinese" else language + " word for bodhisattva"}
སྒོམ་པ་ → {"禅修" if language == "Chinese" else language + " word for meditation"}
ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་ → {"般若波罗蜜多" if language == "Chinese" else language + " word for perfection of wisdom"}
རྣམ་པར་ཤེས་པ་ → {"意识" if language == "Chinese" else language + " word for consciousness"}

[Continue with word-by-word mapping for the entire text]
"""
        prompts.append(prompt)
    
    # Process in batches
    word_by_word_translations = [None] * len(corpus)
    batch_size = 20
    batches = [prompts[i:i + batch_size] for i in range(0, len(prompts), batch_size)]
    batch_indices = [list(range(i, min(i + batch_size, len(prompts)))) for i in range(0, len(prompts), batch_size)]
    
    for batch_idx, (batch, indices) in enumerate(zip(batches, batch_indices)):
        try:
            logger.info(f"🔄 Batch {batch_idx+1}/{len(batches)}: Processing {len(batch)} word-by-word mappings")
            
            # Process the batch
            results = word_by_word_translator.batch(batch)
            
            # Store results
            for i, result in zip(indices, results):
                word_by_word_translations[i] = result.word_by_word_translation
                
        except Exception as e:
            logger.error(f"❌ Error in batch {batch_idx+1}: {str(e)}")
            logger.info(f"🔄 Retrying batch {batch_idx+1}...")
            
            try:
                # Retry once
                results = word_by_word_translator.batch(batch)
                for i, result in zip(indices, results):
                    word_by_word_translations[i] = result.word_by_word_translation
            except Exception as retry_e:
                logger.error(f"❌ Error on retry for batch {batch_idx+1}: {str(retry_e)}")
                
                # Process each item individually
                for idx, (i, prompt) in enumerate(zip(indices, batch)):
                    try:
                        result = word_by_word_translator.invoke(prompt)
                        word_by_word_translations[i] = result.word_by_word_translation
                        logger.debug(f"Successfully processed item {idx+1} individually")
                    except Exception as item_e:
                        logger.error(f"❌ Failed to process item {idx+1}: {str(item_e)}")
                        word_by_word_translations[i] = ""  # Fallback to empty string
    
    # Update corpus with word-by-word translations
    updated_corpus = corpus.copy()
    for i, wbw in enumerate(word_by_word_translations):
        if wbw:
            updated_corpus[i]['word_by_word_translation'] = wbw
    
    logger.info(f"✅ Generated {sum(1 for wbw in word_by_word_translations if wbw)} word-by-word mappings")
    return updated_corpus

def post_process_corpus(corpus: List[Dict[str, Any]], 
                   output_file: str = 'inputs_final_cleaned.json',
                   glossary_file: str = 'standard_translation.csv',
                   language: str = None):
    """
    Main function to run the full post-processing pipeline on a corpus.
    
    Args:
        corpus: List of document dictionaries
        output_file: Path to save the final processed corpus
        glossary_file: Path to save the standardized glossary CSV
        language: Target language for translations (optional, will auto-detect from corpus)
        
    Returns:
        Processed corpus with standardized translations and word-by-word mappings
    """
    logger.info("🚀 Starting post-translation processing")
    
    # Detect language from corpus if not specified
    if language is None:
        # Try to get language from the first document with a language field
        for doc in corpus:
            if 'language' in doc and doc['language']:
                language = doc['language']
                logger.info(f"🌐 Auto-detected language from corpus: {language}")
                break
        
        # Default to English if not found
        if language is None:
            language = 'English'
            logger.info(f"🌐 No language found in corpus, defaulting to: {language}")
    
    # Extract glossaries from all documents
    logger.info("📊 Extracting glossaries from corpus...")
    all_glossaries = []
    for doc in tqdm(corpus, desc="Extracting glossaries"):
        if 'glossary' in doc and doc['glossary']:
            all_glossaries.append(doc['glossary'])
    
    logger.info(f"📊 Extracted glossaries from {len(all_glossaries)} documents")
    
    # Analyze term frequencies
    term_freq_df = analyze_term_frequencies(all_glossaries)
    
    # Generate standardization examples with target language
    logger.info(f"🌐 Generating standardization examples for {language}")
    examples = generate_standardization_examples(term_freq_df, corpus, language=language)
    
    # Standardize terminology with target language
    logger.info(f"🌐 Standardizing terminology in {language}")
    standardized_terms = standardize_terminology(examples, language=language)
    
    # Convert to DataFrame and save
    standardized_df = pd.DataFrame(standardized_terms)
    standardized_df.to_csv(glossary_file, index=False)
    logger.info(f"💾 Saved standardized glossary to {glossary_file}")
    
    # Apply standardized terms to corpus
    updated_corpus = apply_standardized_terms(corpus, standardized_df)
    
    # Generate word-by-word translations
    logger.info(f"🌐 Generating word-by-word translations in {language}")
    final_corpus = generate_word_by_word(updated_corpus, language=language)
    
    # Save final corpus
    logger.info(f"💾 Saving final processed corpus to {output_file}...")
    
    # Determine format based on file extension
    is_jsonl = output_file.endswith('.jsonl')
    
    # Prepare final documents with required fields
    final_output = []
    required_fields = ['source', 'translation', 'combined_commentary', 'word_by_word_translation', 'plaintext_translation']
    
    for doc in final_corpus:
        # Create a new document with only the required fields
        output_doc = {}
        
        # Add required fields, ensuring they exist
        for field in required_fields:
            # Get field value, handling special cases
            field_value = doc.get(field, "")
            
            # Handle translation lists - convert to last translation if needed
            if field == 'translation':
                # Handle list case
                if isinstance(field_value, list) and field_value:
                    field_value = field_value[-1] if field_value else ""
                    logger.debug(f"Converting translation list to single string (using last item) for output")
                
                # Handle JSON string case
                elif isinstance(field_value, str) and (
                    (field_value.startswith('[') and field_value.endswith(']')) or
                    (field_value.startswith('{') and field_value.endswith('}'))
                ):
                    logger.debug(f"Output translation appears to be a JSON string, attempting to parse")
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(field_value)
                        
                        # Handle parsed result based on type
                        if isinstance(parsed, list) and parsed:
                            # Use last item in list
                            field_value = parsed[-1]
                            logger.debug(f"Parsed output translation to list, using last item")
                        
                        elif isinstance(parsed, dict) and 'translation' in parsed:
                            # Use translation field from object
                            field_value = parsed['translation']
                            logger.debug(f"Parsed output translation to object, using translation field")
                        
                        else:
                            # Otherwise use string representation
                            field_value = str(parsed)
                            logger.debug(f"Parsed JSON but using string representation for output")
                    
                    except json.JSONDecodeError:
                        # Keep as is if not valid JSON
                        pass
            
            # For plaintext_translation, make sure it's a string (could be a list or JSON string)
            if field == 'plaintext_translation':
                # Handle list case
                if isinstance(field_value, list) and field_value:
                    # Join all translations with newlines
                    field_value = "\n".join(field_value)
                    logger.debug(f"Converting plaintext_translation list to concatenated string")
                
                # Handle JSON string case
                elif isinstance(field_value, str) and (
                    (field_value.startswith('[') and field_value.endswith(']')) or
                    (field_value.startswith('{') and field_value.endswith('}'))
                ):
                    logger.debug(f"Plaintext translation appears to be a JSON string, attempting to parse")
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(field_value)
                        
                        # Handle parsed result based on type
                        if isinstance(parsed, list) and parsed:
                            # Join all list items with newlines
                            field_value = "\n".join([str(item) for item in parsed])
                            logger.debug(f"Parsed plaintext_translation to list and joined items")
                        
                        elif isinstance(parsed, dict) and 'translation' in parsed:
                            # Use translation field from object
                            field_value = parsed['translation']
                            logger.debug(f"Parsed plaintext_translation to object, using translation field")
                        
                        else:
                            # Otherwise use string representation
                            field_value = str(parsed)
                            logger.debug(f"Parsed JSON but using string representation for plaintext_translation")
                    
                    except json.JSONDecodeError:
                        # Keep as is if not valid JSON
                        pass
            
            # Set the field value
            output_doc[field] = field_value
            
            # If a required field is missing, log a warning
            if not output_doc[field] and field != 'word_by_word_translation':  # word_by_word can be empty
                logger.warning(f"⚠️ Missing required field '{field}' in document")
        
        final_output.append(output_doc)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        if is_jsonl:
            # Save as JSONL (one JSON object per line)
            for doc in final_output:
                json.dump(doc, f, ensure_ascii=False)
                f.write('\n')
            logger.debug(f"Saved {len(final_output)} documents in JSONL format")
        else:
            # Save as regular JSON
            json.dump(final_output, f, ensure_ascii=False, indent=4)
            logger.debug(f"Saved {len(final_output)} documents in JSON format")
    
    logger.info("✅ Post-translation processing complete!")
    logger.info("📊 Results summary:")
    logger.info(f"  - Standardized {len(standardized_terms)} terms")
    logger.info(f"  - Updated {len([doc for doc in final_corpus if doc.get('translation')])} translations")
    logger.info(f"  - Generated {len([doc for doc in final_corpus if doc.get('word_by_word_translation')])} word-by-word mappings")
    logger.info(f"  - Output saved to: {output_file}")
    
    return final_corpus