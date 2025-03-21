#!/usr/bin/env python
# coding: utf-8

"""
Glossary Extractor Tool

This script extracts and compiles glossary entries from JSONL files containing
translation states that already have glossary entries.

Usage:
    python generate_glossary.py --input results.jsonl --output glossary.csv

Features:
- Processes one or more JSONL files
- Extracts existing glossary entries from state objects
- Handles entries in any target language
- Deduplicates entries to prevent redundancy
- Compiles all entries into a single CSV file
"""

import argparse
import json
import os
import pandas as pd
from typing import List, Dict, Any
from tqdm import tqdm

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a JSONL file."""
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    records.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"Warning: Error parsing line in {file_path}: {e}")
                    continue
        return records
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return []

def extract_glossary_entries(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract glossary entries from a translation state."""
    # Check if the state has a glossary field
    if 'glossary' not in state or not state['glossary']:
        return []
    
    # Get the glossary entries
    glossary = state['glossary']
    
    # Convert to list of dicts if not already
    if isinstance(glossary, list):
        # Check if the entries are already dictionaries
        if glossary and isinstance(glossary[0], dict):
            return glossary
        
        # Convert from other formats if needed
        entries = []
        for entry in glossary:
            if hasattr(entry, 'dict'):
                # Handle Pydantic model that was serialized
                entries.append(entry.dict())
            elif hasattr(entry, '__dict__'):
                # Handle objects with __dict__
                entries.append(entry.__dict__)
            else:
                # Try to convert directly
                entries.append(dict(entry))
        return entries
    
    return []

def deduplicate_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate glossary entries based on Tibetan term and translation."""
    if not entries:
        return []
    
    # Create a DataFrame for easier deduplication
    df = pd.DataFrame(entries)
    
    # Make sure all expected columns exist
    required_columns = ['tibetan_term', 'translation']
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        print(f"Warning: Missing columns in glossary entries: {missing}")
        # Add missing columns with empty values
        for col in missing:
            df[col] = ""
    
    # Deduplicate based on Tibetan term and translation
    df = df.drop_duplicates(subset=['tibetan_term', 'translation'])
    
    return df.to_dict('records')

def create_glossary_csv(entries: List[Dict[str, Any]], output_file: str) -> str:
    """Create a CSV file from glossary entries."""
    if not entries:
        print("No glossary entries to save!")
        return ""
    
    # Define column order (use available columns, defaulting to standard ones)
    standard_columns = [
        'tibetan_term', 
        'translation', 
        'category', 
        'context', 
        'commentary_reference', 
        'entity_category'
    ]
    
    # Get actual columns from entries
    actual_columns = list(entries[0].keys())
    
    # Use standard columns that exist in the data
    column_order = [col for col in standard_columns if col in actual_columns]
    
    # Add any columns that aren't in the standard list
    column_order.extend([col for col in actual_columns if col not in standard_columns])
    
    # Create DataFrame and organize columns
    df = pd.DataFrame(entries)
    
    # Ensure all columns exist in the dataframe
    for col in column_order:
        if col not in df.columns:
            df[col] = ""
    
    df = df[column_order]
    
    # Save to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Glossary saved to {output_file} with {len(df)} entries")
    
    return output_file

def compile_glossary_from_jsonl(input_files: List[str], output_file: str) -> None:
    """Compile a glossary from one or more JSONL files containing translation states."""
    all_entries = []
    
    for input_file in input_files:
        print(f"Processing {input_file}...")
        states = load_jsonl(input_file)
        print(f"Found {len(states)} states in {input_file}")
        
        for state in tqdm(states, desc="Extracting glossary entries"):
            entries = extract_glossary_entries(state)
            all_entries.extend(entries)
    
    if not all_entries:
        print("No glossary entries found in any of the input files!")
        return
    
    # Deduplicate entries
    unique_entries = deduplicate_entries(all_entries)
    print(f"Extracted {len(all_entries)} entries, {len(unique_entries)} unique entries")
    
    # Create CSV
    create_glossary_csv(unique_entries, output_file)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Extract and compile glossary entries from translation states")
    parser.add_argument("--input", type=str, nargs='+', required=True, 
                        help="Input JSONL file(s) containing translation states with glossary entries")
    parser.add_argument("--output", type=str, default="glossary.csv", 
                        help="Output CSV file for the compiled glossary")
    
    args = parser.parse_args()
    
    # Check that input files exist
    missing_files = [f for f in args.input if not os.path.exists(f)]
    if missing_files:
        print(f"Error: Input file(s) do not exist: {', '.join(missing_files)}")
        return
    
    compile_glossary_from_jsonl(args.input, args.output)

if __name__ == "__main__":
    main()