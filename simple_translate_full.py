#!/usr/bin/env python3
"""
simple_translate_full.py - A script to translate Tibetan text using Google's Gemini Flash 2.0 model.

This script reads JSON files containing Tibetan text in "root" and "commentary" fields,
translates both fields to the specified target language, and saves the results to new files.
Empty fields are preserved as empty strings. Multiple files can be processed in parallel using multithreading.

Usage:
  python simple_translate_full.py input1.json [input2.json input3.json ...] [--root-only | --commentary-only] [--target-lang LANGUAGE]

Options:
  --root-only         Only translate root text fields, skip commentary fields
  --commentary-only   Only translate commentary fields, skip root text fields (default behavior)
  --target-lang LANG  Target language for translation (default: English)
  --max-workers N     Maximum number of parallel worker threads (default: 3)

Examples:
  python simple_translate_full.py input.json
  python simple_translate_full.py input1.json input2.json input3.json
  python simple_translate_full.py *.json --root-only --target-lang Spanish
  python simple_translate_full.py input.json --target-lang Chinese --max-workers 5

Requirements:
  - google-genai library: pip install google-genai
  - python-dotenv (optional): pip install python-dotenv
"""

import json
import sys
import os
import argparse
import concurrent.futures
import time
from google import genai
from typing import Dict, List, Any, Optional, Tuple

# Translation prompt template
TRANSLATION_PROMPT = """
You are a Tibetan Buddhist scholar and translator with expertise in translating Tibetan Buddhist texts.
Translate the following Tibetan text into clear, accurate {target_lang}.
Maintain the philosophical and technical Buddhist terminology accurately.
Translate with sensitivity to the context of Tibetan Buddhist philosophy.

Tibetan text:
{text}

Translate the above Tibetan text into {target_lang}:
"""

def setup_gemini_client() -> genai.Client:
    """Set up and return a Google Gemini client."""
    # Try to load from .env file first
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Note: dotenv package not installed. Install with 'pip install python-dotenv' to use .env files.")
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set. Set it directly or in a .env file.")
    
    return genai.Client(api_key=api_key)

def translate_text(client: genai.Client, text: str, target_lang: str = "English") -> str:
    """Translate Tibetan text to the target language using Gemini."""
    if not text.strip():
        return ""
    
    prompt = TRANSLATION_PROMPT.format(text=text, target_lang=target_lang)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=prompt,
        config={
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4096,
        }
    )
    
    return response.text

def process_json_file(client: genai.Client, input_file: str, output_file: str, 
                      translate_root: bool = False, translate_commentary: bool = True,
                      target_lang: str = "English") -> Tuple[str, str, bool]:
    """
    Process a JSON file, translating specified fields.
    
    Returns:
        Tuple of (input_file, output_file, success)
    """
    try:
        print(f"Reading input file: {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {input_file} is not a valid JSON file")
            return input_file, output_file, False
        except FileNotFoundError:
            print(f"Error: File {input_file} not found")
            return input_file, output_file, False
        
        # Check if data is a list or a single object
        items = data if isinstance(data, list) else [data]
        
        total_items = len(items)
        print(f"Found {total_items} items to process in {input_file}")
        
        # Create field names based on target language
        if target_lang.lower() == "english":
            commentary_field = "commentary_english"
            root_field = "root_english"
        else:
            commentary_field = f"commentary_{target_lang.lower()}"
            root_field = f"root_{target_lang.lower()}"
        
        for i, item in enumerate(items):
            print(f"Processing item {i+1}/{total_items} in {input_file}")
            
            # Translate commentary if enabled
            if translate_commentary and "commentary" in item:
                if item["commentary"].strip():
                    print(f"Translating commentary for item {i+1} in {input_file}")
                    item[commentary_field] = translate_text(client, item["commentary"], target_lang)
                else:
                    item[commentary_field] = ""
            
            # Translate root text if enabled
            if translate_root and "root" in item:
                if item["root"].strip():
                    print(f"Translating root text for item {i+1} in {input_file}")
                    item[root_field] = translate_text(client, item["root"], target_lang)
                else:
                    item[root_field] = ""
        
        # Save the processed data to the output file
        print(f"Saving results to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Translation completed successfully for {input_file}")
        return input_file, output_file, True
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return input_file, output_file, False

def generate_output_filename(input_file: str, target_lang: str, translate_root: bool, translate_commentary: bool) -> str:
    """Generate output filename based on input filename, target language, and translation options."""
    # Split the input filename into base and extension
    base_name, ext = os.path.splitext(input_file)
    
    # Format target language for filename (lowercase, no spaces)
    target_lang_formatted = target_lang.lower().replace(" ", "_")
    
    # Add translation type information
    translation_type = ""
    if translate_root and translate_commentary:
        translation_type = "full"
    elif translate_root:
        translation_type = "root"
    else:  # Default to commentary
        translation_type = "commentary"
    
    # Create the new filename
    return f"{base_name}_translated_{translation_type}_{target_lang_formatted}{ext}"

def process_file_wrapper(args):
    """Wrapper function for process_json_file to use with ThreadPoolExecutor."""
    client, input_file, translate_root, translate_commentary, target_lang = args
    output_file = generate_output_filename(input_file, target_lang, translate_root, translate_commentary)
    return process_json_file(
        client, 
        input_file, 
        output_file, 
        translate_root=translate_root, 
        translate_commentary=translate_commentary,
        target_lang=target_lang
    )

def main():
    parser = argparse.ArgumentParser(description="Translate Tibetan Buddhist texts using Google's Gemini model.")
    parser.add_argument("input_files", nargs='+', help="Input JSON file paths")
    parser.add_argument("--root-only", action="store_true", help="Only translate root text fields")
    parser.add_argument("--commentary-only", action="store_true", help="Only translate commentary fields (default)")
    parser.add_argument("--target-lang", default="English", help="Target language for translation (default: English)")
    parser.add_argument("--max-workers", type=int, default=3, help="Maximum number of parallel worker threads (default: 3)")
    
    args = parser.parse_args()
    
    # Determine what to translate
    translate_root = not args.commentary_only or args.root_only
    translate_commentary = not args.root_only or args.commentary_only
    
    # If both options are specified or neither is specified,
    # use the default (translate commentary only)
    if args.root_only and args.commentary_only:
        print("Warning: Both --root-only and --commentary-only specified. Translating both.")
    elif not args.root_only and not args.commentary_only:
        translate_root = False
        translate_commentary = True
    
    # Set up Gemini client
    try:
        client = setup_gemini_client()
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure to set the GOOGLE_API_KEY environment variable or use a .env file")
        sys.exit(1)
    
    # Process files in parallel
    start_time = time.time()
    translation_type = "full" if translate_root and translate_commentary else "root" if translate_root else "commentary"
    print(f"Starting {translation_type} translation of {len(args.input_files)} files to {args.target_lang} using {args.max_workers} workers")
    
    # Create a list of arguments for each file
    process_args = [
        (client, input_file, translate_root, translate_commentary, args.target_lang) 
        for input_file in args.input_files
    ]
    
    # Process files in parallel using ThreadPoolExecutor
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(process_file_wrapper, arg) for arg in process_args]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"An error occurred: {str(e)}")
    
    # Report results
    successful = sum(1 for _, _, success in results if success)
    failed = len(results) - successful
    
    elapsed_time = time.time() - start_time
    print(f"\nTranslation completed in {elapsed_time:.2f} seconds")
    print(f"Successfully processed: {successful} files")
    
    if failed > 0:
        print(f"Failed to process: {failed} files")
        for input_file, _, success in results:
            if not success:
                print(f"  - {input_file}")
    
    if successful > 0:
        print("\nSuccessfully translated files:")
        for input_file, output_file, success in results:
            if success:
                print(f"  - {input_file} -> {output_file}")

if __name__ == "__main__":
    main()