#!/usr/bin/env python3
"""
Simple Zero-Shot Tibetan Translator

This script provides a simple standalone translator for Tibetan texts
with minimal dependencies. It processes JSON files with "root" and "commentary"
fields, translating only the non-empty commentary fields.
"""

import json
import os
import sys
import argparse
from typing import List, Dict, Any

# Import anthropic if available
try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic package not found.")
    print("Install with: pip install anthropic")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Simple Tibetan Translator")
    parser.add_argument("--input", required=True, help="Input JSON file with Tibetan texts")
    parser.add_argument("--output", help="Output JSON file (default: input_translated.json)")
    parser.add_argument("--language", default="English", help="Target language (default: English)")
    parser.add_argument("--api-key", help="Anthropic API key (if not in .env)")
    return parser.parse_args()

def load_input_data(file_path: str) -> List[Dict[str, Any]]:
    """Load input data from JSON file."""
    print(f"Loading input data from {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        data = [data]  # Convert single document to list
        
    return data

def save_output_data(data: List[Dict[str, Any]], file_path: str):
    """Save output data to JSON file."""
    print(f"Saving results to {file_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def translate_text(client, text: str, language: str) -> str:
    """Translate a text using Anthropic's Claude."""
    if not text.strip():
        return ""
        
    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            temperature=0,
            system="You are an expert translator of Tibetan Buddhist texts. Translate the given Tibetan text directly into the target language without adding any commentary, explanations, or notes. Provide ONLY the translation, nothing else.",
            messages=[
                {
                    "role": "user", 
                    "content": f"Translate this Tibetan text into {language}:\n\n{text}\n\nImportant: Return ONLY the translation, with no introduction, explanation, or notes."
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error during translation: {str(e)}")
        return f"Translation error: {str(e)}"

def process_documents(client, documents: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
    """Process all documents, translating non-empty commentaries."""
    results = []
    
    for i, doc in enumerate(documents):
        print(f"Processing document {i+1}/{len(documents)}")
        result = dict(doc)  # Copy the original document
        
        # Only translate non-empty commentaries
        if "commentary" in doc and doc["commentary"].strip():
            print(f"  - Translating commentary")
            result["commentary"] = translate_text(client, doc["commentary"], language)
        
        results.append(result)
    
    return results

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Set default output file if not provided
    if not args.output:
        base_name = os.path.splitext(os.path.basename(args.input))[0]
        args.output = f"{base_name}_translated.json"
    
    # Get API key - first try command line, then environment variable
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: No Anthropic API key provided.")
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key option.")
        sys.exit(1)
    
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Load input data
    try:
        documents = load_input_data(args.input)
    except Exception as e:
        print(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    print(f"Processing {len(documents)} documents in {args.language}")
    
    # Process documents
    try:
        results = process_documents(client, documents, args.language)
    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        sys.exit(1)
    
    # Save results
    try:
        save_output_data(results, args.output)
    except Exception as e:
        print(f"Error saving output file: {str(e)}")
        sys.exit(1)
    
    print(f"Processing complete. Results saved to {args.output}")

if __name__ == "__main__":
    main()