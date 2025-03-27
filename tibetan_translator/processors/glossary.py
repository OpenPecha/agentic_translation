import json
import logging
import pandas as pd
from typing import List, Any
from tibetan_translator.models import State, GlossaryEntry, GlossaryExtraction
from tibetan_translator.prompts import get_glossary_extraction_prompt
from tibetan_translator.utils import llm, logger

# Create glossary-specific logger
glossary_logger = logging.getLogger("tibetan_translator.glossary")

# Add file handler to avoid console output interfering with tqdm
if not glossary_logger.handlers:
    file_handler = logging.FileHandler("glossary_debug.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    glossary_logger.addHandler(file_handler)
    # Don't propagate to avoid duplicate logs
    glossary_logger.propagate = False


def extract_glossary(state: State) -> List[GlossaryEntry]:
    """Extract technical terms and their translations into a glossary."""
    language = state.get('language', 'English')
    commentary_source = state.get('commentary_source', 'traditional')
    glossary_logger.info(f"Extracting glossary for language: {language}, commentary source: {commentary_source}")
    
    try:
        glossary_prompt = get_glossary_extraction_prompt(
            state['source'], state['combined_commentary'], state['translation'][-1],
            language=language, commentary_source=commentary_source
        )
        
        # Log the language and target language-specific instructions
        glossary_logger.debug(f"Using {language} for glossary extraction")
        
        # Create structured output extractor
        extractor = llm.with_structured_output(GlossaryExtraction)
        glossary_logger.debug("Created structured output extractor for GlossaryExtraction")
        
        # Invoke the model with error handling
        try:
            glossary_logger.debug("Invoking LLM for glossary extraction")
            result = extractor.invoke(glossary_prompt)
            glossary_logger.debug(f"LLM returned result type: {type(result)}")
            
            # Check structure of result
            if hasattr(result, 'entries'):
                entries = result.entries
                glossary_logger.info(f"Successfully extracted {len(entries)} glossary entries")
                glossary_logger.debug(f"Entries type: {type(entries)}")
                
                # Log a sample of the entries for debugging
                if entries and len(entries) > 0:
                    glossary_logger.debug(f"First entry sample: {entries[0]}")
                
                return entries
            else:
                glossary_logger.error(f"LLM result does not have entries attribute: {result}")
                return []
                
        except Exception as e:
            glossary_logger.error(f"Error during LLM invocation: {str(e)}")
            
            # If we're processing Chinese, try to handle the raw response
            if language == "Chinese":
                glossary_logger.warning("Attempting to recover from Chinese processing error")
                try:
                    # Try to get raw completion without structured output
                    raw_response = llm.invoke(glossary_prompt)
                    glossary_logger.debug(f"Raw response type: {type(raw_response)}")
                    
                    # Extract content from AIMessage if needed
                    response_text = ""
                    if hasattr(raw_response, 'content'):
                        response_text = raw_response.content
                        glossary_logger.debug(f"Extracted content from AIMessage: {response_text[:200]}...")
                    elif isinstance(raw_response, str):
                        response_text = raw_response
                    
                    # Try to extract JSON from the response
                    if response_text:
                        # Look for JSON pattern
                        import re
                        json_pattern = r'\[\s*\{.*\}\s*\]'
                        json_matches = re.search(json_pattern, response_text, re.DOTALL)
                        
                        if json_matches:
                            json_str = json_matches.group(0)
                            glossary_logger.debug(f"Found JSON pattern in response: {json_str[:200]}...")
                            
                            try:
                                # Try to clean up the JSON string for better parsing
                                # Remove any non-JSON text that might have been included
                                clean_json = json_str.strip()
                                glossary_logger.debug(f"Cleaned JSON: {clean_json[:200]}...")
                                
                                # Parse the JSON
                                entries_list = json.loads(clean_json)
                                glossary_logger.debug(f"Parsed JSON to list with {len(entries_list)} items")
                                
                                # Convert to GlossaryEntry objects
                                entries = []
                                for entry in entries_list:
                                    try:
                                        # Log each entry for debugging
                                        glossary_logger.debug(f"Processing entry: {entry}")
                                        
                                        # Ensure all required fields exist
                                        required_fields = ['tibetan_term', 'translation', 'context', 
                                                          'commentary_reference', 'category', 'entity_category']
                                        for field in required_fields:
                                            if field not in entry:
                                                entry[field] = ""
                                        
                                        # Create GlossaryEntry object
                                        glossary_entry = GlossaryEntry(**entry)
                                        entries.append(glossary_entry)
                                    except Exception as entry_e:
                                        glossary_logger.error(f"Error processing entry {entry}: {str(entry_e)}")
                                
                                if entries:
                                    glossary_logger.info(f"Recovered {len(entries)} entries from raw response")
                                    return entries
                                else:
                                    glossary_logger.warning("No valid entries could be created from JSON")
                            except Exception as json_e:
                                glossary_logger.error(f"Failed to parse extracted JSON: {str(json_e)}")
                                
                        # Try one more approach - look for a complete JSON array structure
                        try:
                            # Find anything that looks like a complete JSON array
                            array_pattern = r'\[\s*\{[^\[\]]*\}\s*(?:,\s*\{[^\[\]]*\}\s*)*\]'
                            array_matches = re.search(array_pattern, response_text, re.DOTALL)
                            
                            if array_matches:
                                array_json = array_matches.group(0)
                                glossary_logger.debug(f"Found complete JSON array: {array_json[:200]}...")
                                
                                # Parse the JSON
                                entries_list = json.loads(array_json)
                                
                                # Create GlossaryEntry objects
                                entries = []
                                for entry in entries_list:
                                    # Ensure all required fields
                                    required_fields = ['tibetan_term', 'translation', 'context', 
                                                      'commentary_reference', 'category', 'entity_category']
                                    for field in required_fields:
                                        if field not in entry:
                                            entry[field] = ""
                                            
                                    entries.append(GlossaryEntry(**entry))
                                
                                glossary_logger.info(f"Recovered {len(entries)} entries from complete JSON array")
                                return entries
                        except Exception as array_e:
                            glossary_logger.error(f"Failed to parse complete JSON array: {str(array_e)}")
                    
                except Exception as recovery_e:
                    glossary_logger.error(f"Failed recovery attempt: {str(recovery_e)}")
            
            # Return empty list if all else fails
            glossary_logger.warning("Returning empty glossary entries list due to errors")
            return []
    
    except Exception as outer_e:
        glossary_logger.error(f"Error in extract_glossary: {str(outer_e)}")
        return []


def generate_glossary_csv(entries: List[GlossaryEntry], filename: str = "translation_glossary.csv"):
    """Generate or append to a CSV file from glossary entries."""
    glossary_logger.debug(f"Generating CSV from {len(entries)} entries")
    
    # Safety check - if no entries, create a minimal placeholder
    if not entries:
        glossary_logger.warning("No entries provided to generate_glossary_csv, creating placeholder")
        # Create a minimal placeholder entry to prevent DataFrame errors
        placeholder = GlossaryEntry(
            tibetan_term="[placeholder]",
            translation="[no translation available]",
            context="[context unavailable]",
            commentary_reference="[no reference available]",
            category="[unknown]",
            entity_category=""
        )
        entries = [placeholder]
    
    try:
        # Convert entries to dictionaries
        entry_dicts = []
        for entry in entries:
            try:
                entry_dict = entry.dict()
                entry_dicts.append(entry_dict)
            except Exception as e:
                glossary_logger.error(f"Error converting entry to dict: {str(e)}")
                
        # Create DataFrame
        new_df = pd.DataFrame(entry_dicts)
        
        # Ensure all required columns exist
        column_order = ['tibetan_term', 'translation', 'category', 'context', 'commentary_reference', 'entity_category']
        for col in column_order:
            if col not in new_df.columns:
                glossary_logger.warning(f"Column '{col}' missing, adding empty column")
                new_df[col] = ""
                
        # Reorder columns
        new_df = new_df[column_order]
        
        # Save to CSV
        try:
            existing_df = pd.read_csv(filename, encoding='utf-8')
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(filename, index=False, encoding='utf-8')
        except FileNotFoundError:
            new_df.to_csv(filename, index=False, encoding='utf-8')
        
        return filename
        
    except Exception as e:
        glossary_logger.error(f"Error in generate_glossary_csv: {str(e)}")
        # Create an empty CSV with the right structure as fallback
        fallback_df = pd.DataFrame(columns=column_order)
        fallback_df.to_csv(filename, index=False, encoding='utf-8')
        return filename


def generate_glossary(state: State):
    """Generate glossary and save to CSV."""
    glossary_logger.info(f"Generating glossary for language: {state.get('language', 'English')}")
    
    try:
        # Extract glossary entries
        entries = extract_glossary(state)
        glossary_logger.info(f"Extracted {len(entries)} glossary entries")
        
        # Generate CSV file
        filename = generate_glossary_csv(entries)
        glossary_logger.info(f"Saved glossary to {filename}")
        
        # Make sure to preserve plaintext_translation in the return state
        return {
            "glossary": entries,
            "plaintext_translation": state.get("plaintext_translation", "")
        }
    except Exception as e:
        glossary_logger.error(f"Error in generate_glossary: {str(e)}")
        # Return empty glossary to prevent workflow failures
        return {
            "glossary": [],
            "plaintext_translation": state.get("plaintext_translation", "")
        }
