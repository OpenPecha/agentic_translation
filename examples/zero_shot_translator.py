#!/usr/bin/env python3
"""
Zero-Shot Tibetan Translator

This script implements a simplified batch translator that uses direct LLM calls
with few-shot prompting, without the full LangGraph workflow. It processes
multiple texts in parallel using batch capabilities.
"""

import argparse
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from tibetan_translator.utils import (
    llm, 
    get_plain_translation_prompt,
    get_combined_commentary_prompt, 
    get_zero_shot_commentary_prompt,
    translation_extraction_examples,
)
from tibetan_translator.config import MAX_TOKENS
from tibetan_translator.models import Translation_extractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zero_shot_translation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("zero_shot_translator")

def setup_argparse() -> argparse.Namespace:
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(description="Zero-shot Tibetan translator with batch processing")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with Tibetan texts")
    parser.add_argument("--output", type=str, default=None, help="Output JSONL file (default: input_translated.jsonl)")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for processing texts")
    parser.add_argument("--language", type=str, default="English", help="Target language for translation")
    parser.add_argument("--no-commentary", action="store_true", help="Skip commentary generation")
    
    return parser.parse_args()

def load_input_data(file_path: str) -> List[Dict[str, Any]]:
    """Load input data from JSON or JSONL file."""
    logger.info(f"Loading input data from {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
        # Handle JSONL format (multiple JSON objects, one per line)
        if content.startswith("{") and "\n{" in content:
            return [json.loads(line) for line in content.splitlines() if line.strip()]
        
        # Handle JSON array
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]  # Single document
        else:
            raise ValueError(f"Unsupported input format in {file_path}")

def save_results(results: List[Dict[str, Any]], output_file: str):
    """Save translation results maintaining original file format."""
    logger.info(f"Saving results to {output_file}")
    
    # Determine if we should use JSON or JSONL format based on extension
    if output_file.endswith('.jsonl'):
        # Save as JSONL format (one object per line)
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        # Save as JSON format (array of objects)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

def create_batches(items: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
    """Create batches of items for efficient processing."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

def preprocess_documents(documents: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
    """Preprocess documents to standardize fields for root/commentary format."""
    processed = []
    
    for doc in documents:
        # Create a processed document with language
        processed_doc = {"language": language}
        
        # Store the original document to preserve structure
        processed_doc["original_doc"] = doc
        
        # Handle root field - store content for translation
        if "root" in doc:
            processed_doc["source"] = doc["root"] if doc["root"] else ""
            processed_doc["has_root"] = bool(doc["root"])
        else:
            processed_doc["source"] = ""
            processed_doc["has_root"] = False
            
        # Handle commentary field - always include for translation if the key exists
        if "commentary" in doc:
            processed_doc["commentary"] = doc["commentary"] if doc["commentary"] else ""
            # Flag if the commentary key exists, regardless of content
            processed_doc["has_commentary_key"] = True
            # Always translate non-empty commentary, even if it's just one character
            processed_doc["has_commentary_content"] = bool(doc["commentary"])
        else:
            processed_doc["commentary"] = ""
            processed_doc["has_commentary_key"] = False
            processed_doc["has_commentary_content"] = False
        
        # Add to processed list - include ALL documents regardless of content
        processed.append(processed_doc)
        
    return processed

def generate_commentaries_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate commentaries for a batch of documents using LLM batching."""
    # Prepare prompts for each document
    prompts = []
    # Keep track of which documents have commentary keys and content
    commentary_status = []
    
    for doc in batch:
        # Save commentary status for each document
        status = {
            "has_key": doc.get("has_commentary_key", False),
            "has_content": doc.get("has_commentary_content", False)
        }
        commentary_status.append(status)
        
        # Create appropriate prompt based on content
        if "commentary" in doc and doc["commentary"]:
            # Create direct translation prompt for ANY non-empty commentary
            original_commentary = doc.get("commentary", "")
            
            # Use a simpler, direct translation prompt
            system_message = SystemMessage(content=f"""You are an expert translator of Tibetan Buddhist texts into {doc["language"]}. 
Translate the provided Tibetan text directly without adding any explanation, commentary, or notes.
Provide ONLY the translation in {doc["language"]}, nothing else.""")
            
            user_message = HumanMessage(content=f"""Translate this Tibetan text into {doc["language"]}:

{original_commentary}

Important: Return ONLY the translation, no introduction, no explanations, no notes.""")
            
            prompt = [system_message, user_message]
        else:
            # Only use None for truly empty commentaries
            prompt = None
            
        prompts.append(prompt)
    
    # Filter out None prompts and remember their indices
    valid_prompts = []
    valid_indices = []
    for i, prompt in enumerate(prompts):
        if prompt is not None:
            valid_prompts.append(prompt)
            valid_indices.append(i)
    
    # Call LLM in batch mode only for valid prompts
    if valid_prompts:
        logger.info(f"Generating commentaries for {len(valid_prompts)} documents with content")
        responses = llm.batch(valid_prompts)
    else:
        responses = []
    
    # Process responses and rebuild full results list
    results = [{"combined_commentary": None} for _ in range(len(batch))]
    
    # Fill in results for the valid prompts
    for i, response_idx in enumerate(valid_indices):
        try:
            if i < len(responses):
                results[response_idx] = {"combined_commentary": responses[i].content}
        except Exception as e:
            logger.error(f"Error processing commentary response: {str(e)}")
    
    # For documents that have commentary key but no content, use empty string
    for i, status in enumerate(commentary_status):
        if status["has_key"] and not status["has_content"]:
            results[i] = {"combined_commentary": ""}
            
    return results

def generate_translations_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate plain translations for a batch of documents using LLM batching."""
    # Prepare prompts for each document
    prompts = []
    for doc in batch:
        # Only create prompts for non-empty sources
        if doc.get("source", "").strip():
            # Create direct translation prompt
            system_message = SystemMessage(content=f"""You are an expert translator of Tibetan Buddhist texts into {doc["language"]}. 
Translate the provided Tibetan text directly without adding any explanation, commentary, or notes.
Provide ONLY the translation in {doc["language"]}, nothing else.""")
            
            user_message = HumanMessage(content=f"""Translate this Tibetan text into {doc["language"]}:

{doc["source"]}

Important: Return ONLY the translation, no introduction, no explanations, no notes.""")
            
            prompt = [system_message, user_message]
        else:
            # Empty source gets empty translation
            prompt = None
            
        prompts.append(prompt)
    
    # Filter out None prompts and remember their indices
    valid_prompts = []
    valid_indices = []
    for i, prompt in enumerate(prompts):
        if prompt is not None:
            valid_prompts.append(prompt)
            valid_indices.append(i)
    
    # Call LLM in batch mode only for valid prompts
    if valid_prompts:
        logger.info(f"Generating translations for {len(valid_prompts)} documents with content")
        responses = llm.batch(valid_prompts)
    else:
        responses = []
    
    # Process responses and rebuild full results list
    results = [{"translation": ""} for _ in range(len(batch))]
    
    # Fill in results for the valid prompts
    for i, response_idx in enumerate(valid_indices):
        try:
            if i < len(responses):
                results[response_idx] = {"translation": responses[i].content}
        except Exception as e:
            logger.error(f"Error processing translation response: {str(e)}")
            
    return results

# Glossary extraction removed to focus on translation only

def batch_translate_documents(
    documents: List[Dict[str, Any]], 
    batch_size: int,
    language: str,
    skip_commentary: bool = False
) -> List[Dict[str, Any]]:
    """Process documents in batches, generating translations and commentaries."""
    # Create batches
    batches = create_batches(documents, batch_size)
    processed_documents = []
    
    for batch_idx, batch in enumerate(tqdm(batches, desc="Processing batches")):
        logger.info(f"Processing batch {batch_idx+1}/{len(batches)}")
        
        # Step 1: Generate commentaries (unless skipped)
        if not skip_commentary:
            try:
                commentary_results = generate_commentaries_batch(batch)
                
                # Update documents with commentaries
                for i, doc in enumerate(batch):
                    # Check if this is a completely empty commentary 
                    original_doc = doc.get("original_doc", {})
                    if "commentary" in original_doc and not original_doc["commentary"]:
                        # Only keep completely empty commentaries as empty strings
                        doc["combined_commentary"] = ""
                    else:
                        # Use the translation for ANY non-empty commentary
                        doc["combined_commentary"] = commentary_results[i]["combined_commentary"]
            except Exception as e:
                logger.error(f"Error in commentary batch {batch_idx+1}: {str(e)}")
                
                # Fall back to empty commentaries
                for doc in batch:
                    doc["combined_commentary"] = ""
        
        # Step 2: Generate translations
        try:
            translation_results = generate_translations_batch(batch)
            
            # Update documents with translations
            for i, doc in enumerate(batch):
                doc["translation"] = translation_results[i]["translation"]
        except Exception as e:
            logger.error(f"Error in translation batch {batch_idx+1}: {str(e)}")
            
            # Fall back to individual processing
            for i, doc in enumerate(batch):
                try:
                    prompt = get_plain_translation_prompt(doc["source"], language=doc["language"])
                    response = llm.invoke(prompt)
                    doc["translation"] = response.content
                except Exception as item_e:
                    logger.error(f"Individual translation failed: {str(item_e)}")
                    doc["translation"] = "Translation failed"
        
        # Add processed batch to results
        processed_documents.extend(batch)
    
    return processed_documents

def main():
    """Main function to run the zero-shot translator."""
    # Parse command line arguments
    args = setup_argparse()
    
    # Set default output file if not provided
    if args.output is None:
        input_path = args.input
        input_base = os.path.splitext(os.path.basename(input_path))[0]
        input_ext = os.path.splitext(os.path.basename(input_path))[1]
        # Keep same extension as input file
        args.output = f"{input_base}_translated{input_ext}"
    
    # Load and preprocess input data
    input_data = load_input_data(args.input)
    documents = preprocess_documents(input_data, args.language)
    
    logger.info(f"Processing {len(documents)} documents in batches of {args.batch_size}")
    logger.info(f"Target language: {args.language}")
    
    # Process documents in batches
    processed_documents = batch_translate_documents(
        documents, 
        args.batch_size,
        args.language,
        skip_commentary=args.no_commentary
    )
    
    # Format results back to original structure
    output_documents = []
    for doc in processed_documents:
        # Get the original document to maintain exact structure
        original_doc = doc.get("original_doc", {})
        output_doc = dict(original_doc)  # Start with a copy of the original document
        
        # Replace commentary with translation if the key exists
        if "commentary" in original_doc:
            # If original commentary is completely empty, keep it empty
            if not original_doc["commentary"]:
                output_doc["commentary"] = ""
            else:
                # Replace ANY non-empty commentary with translation, even if just whitespace
                combined_commentary = doc.get("combined_commentary")
                if combined_commentary is not None:
                    output_doc["commentary"] = combined_commentary
        
        output_documents.append(output_doc)
    
    # Save results
    save_results(output_documents, args.output)
    logger.info(f"Completed processing. Results saved to {args.output}")

if __name__ == "__main__":
    main()