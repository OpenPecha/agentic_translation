#!/usr/bin/env python
"""
Post-Translation Example

This script demonstrates how to use the post-translation processing module
to standardize terminology, generate word-by-word translations, and produce
a finalized corpus of translations.

Usage:
    python examples/post_translation_example.py --input sample_corpus.json --output final_corpus.json
"""

import argparse
import json
import os
import sys
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path so we can import the tibetan_translator package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import post-translation module
from tibetan_translator.processors.post_translation import (
    post_process_corpus,
    analyze_term_frequencies,
    generate_standardization_examples,
    standardize_terminology,
    apply_standardized_terms,
    generate_word_by_word,
    logger
)

def load_corpus(file_path: str) -> List[Dict[str, Any]]:
    """Load corpus from JSON or JSONL file."""
    corpus = []
    
    try:
        # Check if file is JSONL (based on extension or content)
        is_jsonl = file_path.endswith('.jsonl')
        
        if is_jsonl:
            # Load JSONL file line by line
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    try:
                        # Parse each line as a separate JSON object
                        doc = json.loads(line)
                        corpus.append(doc)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON on line {i}: {str(e)}")
                        logger.error(f"Line content (first 100 chars): {line[:100]}...")
        else:
            # Load regular JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                corpus = json.load(f)
        
        logger.info(f"✅ Loaded corpus with {len(corpus)} documents from {file_path}")
        return corpus
        
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        if not is_jsonl:  # Only for JSON files, JSONL errors are handled line by line
            logger.error(f"❌ Invalid JSON in file: {file_path}")
            logger.error(f"Error details: {str(e)}")
            sys.exit(1)

def sample_workflow():
    """
    Run a sample post-translation workflow with test data.
    """
    # Create a minimal test corpus if none is available
    test_corpus = [
        {
            "source": "བྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་།",
            "translation": "The tree of bodhicitta constantly produces fruit.",
            "sanskrit": "bodhicittadruma sadā",
            "language": "English",
            "glossary": [
                {
                    "tibetan_term": "བྱང་ཆུབ་སེམས",
                    "translation": "bodhicitta",
                    "context": "The awakening mind",
                    "commentary_reference": "From Śāntideva",
                    "category": "philosophical",
                    "entity_category": ""
                },
                {
                    "tibetan_term": "ལྗོན་ཤིང",
                    "translation": "tree",
                    "context": "Metaphor for growth",
                    "commentary_reference": "In Bodhicaryāvatāra",
                    "category": "metaphorical",
                    "entity_category": ""
                }
            ],
            "combined_commentary": "The tree of bodhicitta is a metaphor for the mind of awakening."
        },
        {
            "source": "བྱང་ཆུབ་སེམས་ནི་ཡོན་ཏན་ཀུན་གྱི་གཞི།",
            "translation": "The awakening mind is the foundation of all qualities.",
            "sanskrit": "bodhicittaṃ sarva guṇānāṃ ādhāra",
            "language": "English",
            "glossary": [
                {
                    "tibetan_term": "བྱང་ཆུབ་སེམས",
                    "translation": "awakening mind",
                    "context": "The mind aspiring to enlightenment",
                    "commentary_reference": "From Nāgārjuna",
                    "category": "philosophical",
                    "entity_category": ""
                },
                {
                    "tibetan_term": "ཡོན་ཏན",
                    "translation": "qualities",
                    "context": "Positive attributes",
                    "commentary_reference": "In Buddhist context",
                    "category": "philosophical",
                    "entity_category": ""
                }
            ],
            "combined_commentary": "The mind of awakening is the source from which all positive qualities arise."
        }
    ]
    
    # Process the corpus - demonstrating auto-detection of language
    logger.info("🧪 Running sample post-translation workflow...")
    logger.info("🌐 Auto-detecting language from corpus documents...")
    processed_corpus = post_process_corpus(
        test_corpus, 
        output_file="sample_output.json",
        glossary_file="sample_glossary.csv"
        # No language specified - should auto-detect from corpus
    )
    
    logger.info("🔍 Checking results...")
    standardized_terms = set()
    for doc in processed_corpus:
        if 'word_by_word_translation' in doc:
            logger.info("✅ Word-by-word translation generated")
            logger.info(f"Sample: {doc['word_by_word_translation'][:100]}...")
            
        # Extract any standardized terms from doc
        if 'tibetan_term' in doc:
            for term in doc['tibetan_term'].split(', '):
                standardized_terms.add(term)
    
    logger.info(f"Summary: {len(standardized_terms)} standardized terms applied")
    logger.info("✅ Sample workflow completed successfully")

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Post-translation processing example")
    parser.add_argument("--input", type=str, default="", help="Input corpus JSON/JSONL file")
    parser.add_argument("--output", type=str, default="", help="Output corpus file path")
    parser.add_argument("--glossary", type=str, default="standard_translation.csv", 
                      help="Output path for standardized glossary CSV")
    parser.add_argument("--language", type=str, default="English", 
                      help="Target language for translations (default: English)")
    parser.add_argument("--sample", action="store_true", help="Run with sample data")
    parser.add_argument("--force", action="store_true", help="Continue processing even with JSON errors")
    
    args = parser.parse_args()
    
    if args.sample:
        sample_workflow()
    elif args.input:
        # Handle paths with spaces
        input_path = args.input.strip('"\'')
        
        # Set default output path based on input with _final prefix
        output_path = args.output.strip('"\'') if args.output else ""
        if not output_path:
            # Create default output path based on input file
            input_base = Path(input_path).stem
            input_ext = ".jsonl"  # Always use JSONL for output
            output_path = f"{input_base}_final{input_ext}"
        
        logger.info(f"🔍 Input file: {input_path}")
        logger.info(f"📝 Output will be saved to: {output_path}")
        
        try:
            # Load corpus from file
            corpus = load_corpus(input_path)
            
            if not corpus:
                logger.error("❌ No valid documents found in input file")
                sys.exit(1)
                
            # Set glossary path
            glossary_path = args.glossary.strip('"\'')
            logger.info(f"📕 Glossary will be saved to: {glossary_path}")
            
            # Try to detect language from input file name or use the provided one
            detected_language = None
            input_filename = os.path.basename(input_path).lower()
            
            # Check if filename contains language hints
            language_hints = {
                "english": "English",
                "chinese": "Chinese",
                "spanish": "Spanish",
                "french": "French",
                "german": "German", 
                "japanese": "Japanese",
                "hindi": "Hindi",
                "russian": "Russian",
                "arabic": "Arabic"
            }
            
            for hint, lang in language_hints.items():
                if hint in input_filename:
                    detected_language = lang
                    break
            
            # Get target language - either from command line, filename, or let it auto-detect from corpus
            language = args.language if args.language else detected_language
            
            if language:
                logger.info(f"🌐 Target language: {language} {'(auto-detected from filename)' if detected_language else '(specified)'}")
                # Process the corpus with explicit language
                post_process_corpus(corpus, output_path, glossary_path, language=language)
            else:
                logger.info(f"🌐 Language will be auto-detected from corpus documents")
                # Process the corpus and let it auto-detect language
                post_process_corpus(corpus, output_path, glossary_path)
        except Exception as e:
            logger.error(f"❌ Error processing corpus: {str(e)}")
            if args.force:
                logger.warning("⚠️ Continuing despite errors (--force flag is set)")
            else:
                sys.exit(1)
    else:
        logger.error("❌ Please provide an input file with --input or use --sample for sample data")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()