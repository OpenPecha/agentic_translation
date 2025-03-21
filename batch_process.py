#!/usr/bin/env python
# coding: utf-8

import json
import logging
import os
import sys
import time
from tqdm import tqdm
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if API key is set
if "ANTHROPIC_API_KEY" not in os.environ:
    print("Error: ANTHROPIC_API_KEY not found in environment variables.")
    print("Make sure you have a .env file with your API key.")
    sys.exit(1)

from tibetan_translator.utils import convert_state_to_jsonl, get_json_data, logger
from tibetan_translator import optimizer_workflow
from tibetan_translator.models import State

# Add batch processor logger
batch_logger = logging.getLogger("batch_processor")

# Create a separate file handler for batch processor to avoid console output
if not batch_logger.handlers:
    file_handler = logging.FileHandler("batch_processor_debug.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    batch_logger.addHandler(file_handler)
    # Don't propagate to root logger to avoid duplicate messages
    batch_logger.propagate = False

class CustomEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        try:
            if hasattr(obj, '__dict__'):
                batch_logger.debug(f"Converting object with __dict__: {type(obj).__name__}")
                return obj.__dict__
            
            # Log unusual objects that might cause serialization issues
            batch_logger.debug(f"Converting non-dict object: {type(obj).__name__}, value: {str(obj)[:100]}")
            return str(obj)
        except Exception as e:
            batch_logger.error(f"Error in CustomEncoder: {str(e)} for object type {type(obj).__name__}")
            return f"[Error encoding object of type {type(obj).__name__}]"

def convert_state_to_jsonl(state_dict: dict, file_path: str):
    """
    Save the state dictionary in JSONL format, handling custom objects.
    
    Args:
        state_dict (dict): The state dictionary containing translation data.
        file_path (str): The file path to save the JSONL file.
    """
    batch_logger.debug(f"Converting state to JSONL, keys: {list(state_dict.keys())}")
    
    # Check for entries field specifically
    if 'entries' in state_dict:
        batch_logger.debug(f"Entries field type: {type(state_dict['entries'])}")
        batch_logger.debug(f"Entries content: {str(state_dict['entries'])[:200]}...")
    
    try:
        with open(file_path, 'a', encoding='utf-8') as f:  # Append mode for JSONL
            # First try to serialize to string to catch errors before writing
            json_str = json.dumps(state_dict, cls=CustomEncoder, ensure_ascii=False)
            batch_logger.debug(f"Serialized JSON string length: {len(json_str)}")
            
            # Then write to file
            f.write(json_str)
            f.write("\n")
    except Exception as e:
        batch_logger.error(f"Error in convert_state_to_jsonl: {str(e)}")
        # Try to identify which field might be causing the problem
        for key, value in state_dict.items():
            try:
                json.dumps({key: value}, cls=CustomEncoder, ensure_ascii=False)
            except Exception as field_error:
                batch_logger.error(f"Problem field: {key}, error: {str(field_error)}")
        raise

def run_robust_batch_processing(
    data: List[Dict[str, Any]], 
    batch_size: int = 2,
    max_retries: int = 3,
    retry_delay: int = 5,
    run_name: str = "batch_run",
    language: str = "English"
) -> Tuple[List[State], List[Dict[str, Any]]]:
    """
    Run the translation workflow with robust error handling including retries and fallback to serial processing.
    
    Args:
        data (List[Dict]): The list of dictionaries containing the data.
        batch_size (int): The batch size to process.
        max_retries (int): Maximum number of batch retry attempts before falling back to individual processing.
        retry_delay (int): Delay in seconds between retry attempts.
        run_name (str): The name of the run to save the output files.
        language (str): Target language for translation.
    
    Returns:
        Tuple[List[State], List[Dict]]: Tuple containing (successful results, failed items)
    """
    # Preprocess data for the workflow
    examples = []
    for i in tqdm(data, desc="Creating input dictionaries"):
        examples.append({
            "source": i.get("root_display_text", i.get("root", "")),
            "sanskrit": i.get("sanskrit_text", i.get("sanskrit", "")),
            "commentary1": i.get("commentary_1", ""),
            "commentary2": i.get("commentary_2", ""),
            "commentary3": i.get("commentary_3", ""),
            "feedback_history": [],
            "format_feedback_history": [],
            "itteration": 0,
            "format_iteration": 0,
            "formated": False,
            "glossary": [],
            'language': language
        })

    # Create batches of the specified size
    batches = [examples[i:i + batch_size] for i in range(0, len(examples), batch_size)]
    
    # Process each batch with retry logic
    all_results = []
    all_failures = []
    
    for batch_idx, batch in enumerate(tqdm(batches, desc="Processing batches")):
        batch_success = False
        batch_retries = 0
        
        # Try batch processing with multiple retries
        while not batch_success and batch_retries < max_retries:
            try:
                print(f"Processing batch {batch_idx+1}/{len(batches)}, attempt {batch_retries+1}/{max_retries}")
                # Run the workflow on the batch
                results = optimizer_workflow.batch(batch)
                
                # Save results to JSONL file
                for result in results:
                    convert_state_to_jsonl(result, f"{run_name}.jsonl")
                    all_results.append(result)
                
                batch_success = True
                print(f"✅ Batch {batch_idx+1} processed successfully")
                
            except Exception as e:
                batch_retries += 1
                print(f"❌ Error processing batch {batch_idx+1}: {e}")
                
                if batch_retries < max_retries:
                    print(f"Retrying in {retry_delay} seconds... (Attempt {batch_retries+1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"Max batch retries reached for batch {batch_idx+1}. Falling back to individual processing.")
        
        # If batch processing failed after all retries, process items individually
        if not batch_success:
            print(f"Attempting individual processing for failed batch {batch_idx+1}...")
            
            for item_idx, item in enumerate(batch):
                item_success = False
                item_retries = 0
                
                # Try processing each item individually with retries
                while not item_success and item_retries < max_retries:
                    try:
                        print(f"Processing item {item_idx+1}/{len(batch)}, attempt {item_retries+1}/{max_retries}")
                        
                        # Run the workflow on a single item (as a batch of size 1)
                        result = optimizer_workflow.batch([item], debug=True)
                        
                        # Save successful result
                        convert_state_to_jsonl(result[0], f"{run_name}.jsonl")
                        all_results.append(result[0])
                        
                        item_success = True
                        print(f"✅ Item {item_idx+1} processed successfully")
                        
                    except Exception as e:
                        item_retries += 1
                        print(f"❌ Error processing individual item {item_idx+1}: {e}")
                        
                        if item_retries < max_retries:
                            print(f"Retrying in {retry_delay} seconds... (Attempt {item_retries+1}/{max_retries})")
                            time.sleep(retry_delay)
                        else:
                            print(f"Failed to process item after {max_retries} attempts. Saving as failed.")
                            # Add to failures list and save to failure file
                            all_failures.append(item)
                            convert_state_to_jsonl(item, f"{run_name}_fail.jsonl")
    
    print(f"Processing complete: {len(all_results)} successful, {len(all_failures)} failed")
    return all_results, all_failures

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch process Tibetan translations with robust error handling")
    parser.add_argument("--input", type=str, default="test.json", help="Input JSON or JSONL file")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size for processing")
    parser.add_argument("--retries", type=int, default=3, help="Number of retry attempts")
    parser.add_argument("--delay", type=int, default=5, help="Delay in seconds between retries")
    parser.add_argument("--output", type=str, default="batch_results", help="Output file prefix")
    parser.add_argument("--language", type=str, default="English", help="Target translation language")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with additional logging")
    
    args = parser.parse_args()
    
    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        batch_logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        batch_logger.debug("Debug mode enabled")
    
    # Load test data
    try:
        batch_logger.info(f"Loading data from {args.input}")
        test_data = get_json_data(args.input)
        batch_logger.info(f"Loaded {len(test_data)} examples from {args.input}")
        
        # Log structure of first example
        if test_data and len(test_data) > 0:
            batch_logger.debug(f"First item keys: {list(test_data[0].keys())}")
            
            # Specifically check if there are entries and log their type
            if 'entries' in test_data[0]:
                entries = test_data[0]['entries']
                batch_logger.debug(f"First item entries type: {type(entries)}")
                batch_logger.debug(f"First item entries sample: {str(entries)[:200]}...")
        
        print(f"Loaded {len(test_data)} examples from {args.input}")
    except FileNotFoundError:
        batch_logger.error(f"Input file {args.input} not found")
        print(f"Input file {args.input} not found. Please check the path.")
        return
    except json.JSONDecodeError as e:
        batch_logger.error(f"Error decoding JSON from {args.input}: {str(e)}")
        print(f"Error decoding JSON from {args.input}: {str(e)}")
        return
    except Exception as e:
        batch_logger.error(f"Unexpected error loading data: {str(e)}")
        print(f"Unexpected error loading data: {str(e)}")
        return
    
    # Run the robust workflow
    results, failures = run_robust_batch_processing(
        data=test_data,
        batch_size=args.batch_size,
        max_retries=args.retries,
        retry_delay=args.delay,
        run_name=args.output,
        language=args.language
    )
    
    # Print summary
    print(f"\nProcessing Summary:")
    print(f"Total examples: {len(test_data)}")
    print(f"Successfully processed: {len(results)}")
    print(f"Failed to process: {len(failures)}")
    
    if len(results) > 0:
        print(f"Results saved to {args.output}.jsonl")
    if len(failures) > 0:
        print(f"Failed items saved to {args.output}_fail.jsonl")

if __name__ == "__main__":
    main()