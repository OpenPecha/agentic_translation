#!/usr/bin/env python3
"""
simple_translate.py - A script to translate Tibetan text using Google's Gemini Flash 2.0 model.

This script reads JSON files containing Tibetan text in "root" and "commentary" fields,
translates the non-empty commentary fields to the specified target language, and saves the results to new files.
Empty commentaries are preserved as empty strings. Multiple files can be processed in parallel using multithreading.

Usage:
  python simple_translate.py input1.json [input2.json input3.json ...] [--target-lang LANGUAGE]

Examples:
  python simple_translate.py input.json
  python simple_translate.py input1.json input2.json input3.json
  python simple_translate.py *.json --target-lang Spanish
  python simple_translate.py input.json --target-lang Chinese

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

# No longer using string template as we're creating structured conversation history
# in the translate_text function

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
    """Translate Tibetan text to the target language using Gemini with multi-turn examples."""
    if not text.strip():
        return ""
    
    # Create system instructions
    system_instruction = """You are a Tibetan Buddhist scholar and translator with expertise in translating Tibetan texts.
    Translate with sensitivity to the context of Tibetan Buddhist philosophy and terminology.
    Provide ONLY the translation with no explanations or commentary."""
    
    # Create few-shot examples with proper conversation turns using Content objects
    contents = [
        # First example (Tibetan to English)
        {"role": "user", "parts": [{"text": "Translate this Tibetan text to English: འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པའི་སྙིང་པོ།"}]},
        {"role": "model", "parts": [{"text": "The Heart of the Perfection of Wisdom"}]},
        
        # Second example (Tibetan to Hindi)
        {"role": "user", "parts": [{"text": "Translate this Tibetan text to Hindi: བྱང་ཆུབ་སེམས་དཔའ་སེམས་དཔའ་ཆེན་པོ་འཕགས་པ་སྤྱན་རས་གཟིགས་དབང་ཕྱུག་གིས།"}]},
        {"role": "model", "parts": [{"text": "महाबोधिसत्व आर्य अवलोकितेश्वर ने"}]},
        
        # Third example (Tibetan to Chinese)
        {"role": "user", "parts": [{"text": "Translate this Tibetan text to Chinese: ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་ཟབ་མོ་ལ་སྤྱོད་པའི་ཚེ།"}]},
        {"role": "model", "parts": [{"text": "行深般若波羅蜜多時"}]},
        
        # Final user query with the actual text to translate
        {"role": "user", "parts": [{"text": f"Translate this Tibetan text to {target_lang}: {text}"}]}
    ]
    
    # Generate content with the conversation history and system instruction
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=contents,
        config={
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4096,
            "system_instruction": system_instruction
        }
    )
    
    return response.text

def process_json_file(client: genai.Client, input_file: str, output_file: str, target_lang: str = "English") -> Tuple[str, str, bool]:
    """
    Process a JSON file, translating commentary fields.
    
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
        
        for i, item in enumerate(items):
            print(f"Processing item {i+1}/{total_items} in {input_file}")
            
            # Check if commentary field exists and is not empty
            if "commentary" in item and item["commentary"].strip():
                print(f"Translating commentary for item {i+1} in {input_file}")
                translation = translate_text(client, item["commentary"], target_lang)
                
                # Set the appropriate field name based on target language
                if target_lang.lower() == "english":
                    field_name = "commentary_english"
                else:
                    # Create a field name like commentary_spanish, commentary_chinese, etc.
                    field_name = f"commentary_{target_lang.lower()}"
                    
                item[field_name] = translation
            else:
                # Set the appropriate field name based on target language
                if target_lang.lower() == "english":
                    field_name = "commentary_english"
                else:
                    field_name = f"commentary_{target_lang.lower()}"
                    
                item[field_name] = ""
        
        # Save the processed data to the output file
        print(f"Saving results to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Translation completed successfully for {input_file}")
        return input_file, output_file, True
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return input_file, output_file, False

def generate_output_filename(input_file: str, target_lang: str) -> str:
    """Generate output filename based on input filename and target language."""
    # Split the input filename into base and extension
    base_name, ext = os.path.splitext(input_file)
    
    # Format target language for filename (lowercase, no spaces)
    target_lang_formatted = target_lang.lower().replace(" ", "_")
    
    # Create the new filename
    return f"{base_name}_translated_{target_lang_formatted}{ext}"

def process_file_wrapper(args):
    """Wrapper function for process_json_file to use with ThreadPoolExecutor."""
    client, input_file, target_lang = args
    output_file = generate_output_filename(input_file, target_lang)
    return process_json_file(client, input_file, output_file, target_lang)

def main():
    parser = argparse.ArgumentParser(description="Translate Tibetan text using Google's Gemini model")
    parser.add_argument("input_files", nargs='+', help="Input JSON file paths")
    parser.add_argument("--target-lang", default="English", help="Target language for translation (default: English)")
    parser.add_argument("--max-workers", type=int, default=3, help="Maximum number of parallel worker threads (default: 3)")
    
    args = parser.parse_args()
    
    # Set up Gemini client
    try:
        client = setup_gemini_client()
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure to set the GOOGLE_API_KEY environment variable or use a .env file")
        sys.exit(1)
    
    # Process files in parallel
    start_time = time.time()
    print(f"Starting translation of {len(args.input_files)} files to {args.target_lang} using {args.max_workers} workers")
    
    # Create a list of arguments for each file
    process_args = [(client, input_file, args.target_lang) for input_file in args.input_files]
    
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