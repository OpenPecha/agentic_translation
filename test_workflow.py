#!/usr/bin/env python
# coding: utf-8

import json
import os
import sys
from tqdm import tqdm
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if API key is set
if "ANTHROPIC_API_KEY" not in os.environ:
    print("Error: ANTHROPIC_API_KEY not found in environment variables.")
    print("Make sure you have a .env file with your API key.")
    sys.exit(1)

from tibetan_translator.utils import convert_state_to_jsonl, get_json_data
from tibetan_translator import optimizer_workflow
from tibetan_translator.models import State
import json
from typing import Any

class CustomEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

def convert_state_to_jsonl(state_dict: dict, file_path: str):
    """
    Save the state dictionary in JSONL format, handling custom objects.
    
    Args:
        state_dict (dict): The state dictionary containing translation data.
        file_path (str): The file path to save the JSONL file.
    """
    with open(file_path, 'a', encoding='utf-8') as f:  # Append mode for JSONL
        json.dump(state_dict, f, cls=CustomEncoder, ensure_ascii=False)
        f.write("\n")



def run_batch_processing(data: List[Dict[str, Any]], 
                         batch_size: int = 2, 
                         run_name: str = "test_run") -> List[State]:
    """
    Run the translation workflow on the given data in batches.

    Args:
        data (List[Dict]): The list of dictionaries containing the data.
        batch_size (int): The batch size to process.
        run_name (str): The name of the run to save the output files.

    Returns:
        List[State]: List of the processed state objects
    """
    # Preprocess data for the workflow
    examples = []
    for i in tqdm(data, desc="Creating input dictionaries"):
        examples.append({
            "source": i["root_display_text"],
            "sanskrit": i["sanskrit_text"],
            "commentary1": i["commentary_1"],
            "commentary2": i["commentary_2"],
            "commentary3": i["commentary_3"],
            "feedback_history": [],
            "format_feedback_history": [],
            "itteration": 0,
            "format_iteration": 0,
            "formated": False,
            "glossary": [],
            'language': "Italian"
        })

    # Create batches of the specified size
    batches = [examples[i:i + batch_size] for i in range(0, len(examples), batch_size)]
    
    # Process each batch
    all_results = []
    for batch in tqdm(batches, desc="Processing batches"):
        try:
            # Run the workflow on the batch
            results = optimizer_workflow.batch(batch,debug=True)
            
            # Save results to JSONL file
            for result in results:
                convert_state_to_jsonl(result, f"{run_name}.jsonl")
                all_results.append(result)
                
        except Exception as e:
            print(f"Error processing batch: {e}")
            # Save failed batch entries to separate file
            for item in batch:
                convert_state_to_jsonl(item, f"{run_name}_fail.jsonl")
    
    return all_results

def main():
    # Load test data
    try:
        test_data = get_json_data('test_data/test.json')
        print(f"Loaded {len(test_data)} test examples")
    except FileNotFoundError:
        print("Test data file not found. Please check the path.")
        return
    except json.JSONDecodeError:
        print("Error decoding JSON from test file.")
        return
    
    # Run the workflow on the test data
    results = run_batch_processing(
        data=test_data,
        batch_size=4,  # Process one example at a time for testing
        run_name="test_workflow"
    )
    
    # Print summary of results
    print(f"Processed {len(results)} examples")
    print(f"Results saved to test_workflow.jsonl")

if __name__ == "__main__":
    main()