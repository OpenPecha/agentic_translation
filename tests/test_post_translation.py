"""
Tests for the post-translation module.

This module tests the functionality of the post-translation processor,
which standardizes terminology, generates word-by-word translations,
and produces a finalized corpus of translations.
"""

import os
import sys
import json
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import the tibetan_translator package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tibetan_translator.processors.post_translation import (
    analyze_term_frequencies,
    generate_standardization_examples,
    standardize_terminology,
    apply_standardized_terms,
    generate_word_by_word,
    post_process_corpus
)

class TestPostTranslation(unittest.TestCase):
    """Test cases for post-translation processing module."""
    
    def setUp(self):
        """Set up test data."""
        # Sample glossary entries for testing
        self.glossaries = [
            [
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
            [
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
            ]
        ]
        
        # Sample corpus for testing
        self.corpus = [
            {
                "source": "བྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་།",
                "translation": "The tree of bodhicitta constantly produces fruit.",
                "sanskrit": "bodhicittadruma sadā",
                "glossary": self.glossaries[0],
                "combined_commentary": "The tree of bodhicitta is a metaphor for the mind of awakening."
            },
            {
                "source": "བྱང་ཆུབ་སེམས་ནི་ཡོན་ཏན་ཀུན་གྱི་གཞི།",
                "translation": "The awakening mind is the foundation of all qualities.",
                "sanskrit": "bodhicittaṃ sarva guṇānāṃ ādhāra",
                "glossary": self.glossaries[1],
                "combined_commentary": "The mind of awakening is the source from which all positive qualities arise."
            }
        ]
        
        # Expected standardized glossary
        self.standardized_terms = [
            {
                "tibetan_term": "བྱང་ཆུབ་སེམས",
                "standard_translation": "awakening mind",
                "rationale": "This term appears in multiple contexts and 'awakening mind' is more universally applicable.",
                "target_audience": "practitioners, academics, general readers"
            }
        ]
        
        # Convert to DataFrame
        self.standardized_df = pd.DataFrame(self.standardized_terms)
    
    def test_analyze_term_frequencies(self):
        """Test analyzing term frequencies."""
        result = analyze_term_frequencies(self.glossaries)
        
        # Check result structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('tibetan_term', result.columns)
        self.assertIn('translation_freq', result.columns)
        self.assertIn('translation_count', result.columns)
        
        # Check specific term analysis
        bodhicitta_row = result[result['tibetan_term'] == 'བྱང་ཆུབ་སེམས']
        self.assertEqual(len(bodhicitta_row), 1)
        self.assertEqual(bodhicitta_row.iloc[0]['translation_count'], 2)
        
        # Ensure translations are included in frequency string
        self.assertIn('bodhicitta', bodhicitta_row.iloc[0]['translation_freq'])
        self.assertIn('awakening mind', bodhicitta_row.iloc[0]['translation_freq'])
    
    def test_generate_standardization_examples(self):
        """Test generating standardization examples."""
        # First analyze term frequencies
        term_freq = analyze_term_frequencies(self.glossaries)
        
        # Generate examples
        examples = generate_standardization_examples(term_freq, self.corpus)
        
        # Check examples
        self.assertIsInstance(examples, list)
        if examples:  # Only check if examples are generated
            self.assertIsInstance(examples[0], str)
            # Check for key elements in example
            example = examples[0]
            self.assertIn("Usage examples", example)
            self.assertIn("Translation Standardization Protocol", example)
            self.assertIn("བྱང་ཆུབ་སེམས", example)  # Tibetan term
    
    @patch('tibetan_translator.processors.post_translation.llm')
    def test_standardize_terminology(self, mock_llm):
        """Test standardizing terminology with mocked LLM."""
        # Mock the LLM response
        mock_structured_output = MagicMock()
        mock_structured_output.batch.return_value = [
            MagicMock(
                standard_translation="awakening mind",
                tibetan_term="བྱང་ཆུབ་སེམས",
                rationale="This term appears in multiple contexts and 'awakening mind' is more universally applicable.",
                target_audience="practitioners, academics, general readers"
            )
        ]
        mock_llm.with_structured_output.return_value = mock_structured_output
        
        # Test with a simple example
        examples = ["Sample standardization example"]
        result = standardize_terminology(examples)
        
        # Check result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['tibetan_term'], "བྱང་ཆུབ་སེམས")
        self.assertEqual(result[0]['standard_translation'], "awakening mind")
    
    @patch('tibetan_translator.processors.post_translation.llm')
    def test_apply_standardized_terms(self, mock_llm):
        """Test applying standardized terms with mocked LLM."""
        # Mock the LLM response
        mock_structured_output = MagicMock()
        mock_structured_output.batch.return_value = [
            MagicMock(
                standardised_translation="The tree of awakening mind constantly produces fruit."
            )
        ]
        mock_llm.with_structured_output.return_value = mock_structured_output
        
        # Apply standardized terms
        result = apply_standardized_terms([self.corpus[0]], self.standardized_df)
        
        # Check result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        # Verify translation is updated
        self.assertEqual(
            result[0]['translation'], 
            "The tree of awakening mind constantly produces fruit."
        )
    
    @patch('tibetan_translator.processors.post_translation.llm')
    def test_generate_word_by_word(self, mock_llm):
        """Test generating word-by-word translations with mocked LLM."""
        # Mock the LLM response
        mock_structured_output = MagicMock()
        mock_structured_output.batch.return_value = [
            MagicMock(
                word_by_word_translation="བྱང་ཆུབ་སེམས → awakening mind\nལྗོན་ཤིང → tree"
            )
        ]
        mock_llm.with_structured_output.return_value = mock_structured_output
        
        # Generate word-by-word translations
        result = generate_word_by_word([self.corpus[0]])
        
        # Check result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        # Verify word-by-word translation is added
        self.assertIn('word_by_word_translation', result[0])
        self.assertEqual(
            result[0]['word_by_word_translation'], 
            "བྱང་ཆུབ་སེམས → awakening mind\nལྗོན་ཤིང → tree"
        )
    
    @patch('tibetan_translator.processors.post_translation.analyze_term_frequencies')
    @patch('tibetan_translator.processors.post_translation.generate_standardization_examples')
    @patch('tibetan_translator.processors.post_translation.standardize_terminology')
    @patch('tibetan_translator.processors.post_translation.apply_standardized_terms')
    @patch('tibetan_translator.processors.post_translation.generate_word_by_word')
    def test_post_process_corpus(self, mock_wbw, mock_apply, mock_standardize, 
                                mock_generate, mock_analyze):
        """Test the full post-processing pipeline with mocked components."""
        # Mock component responses
        mock_analyze.return_value = pd.DataFrame([
            {'tibetan_term': 'བྱང་ཆུབ་སེམས', 'translation_freq': 'bodhicitta (1);awakening mind (1)', 'translation_count': 2}
        ])
        mock_generate.return_value = ["Sample standardization example"]
        mock_standardize.return_value = self.standardized_terms
        mock_apply.return_value = [
            {
                "source": "བྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་།",
                "translation": "The tree of awakening mind constantly produces fruit.",
                "sanskrit": "bodhicittadruma sadā",
                "glossary": self.glossaries[0],
                "combined_commentary": "The tree of bodhicitta is a metaphor for the mind of awakening."
            }
        ]
        mock_wbw.return_value = [
            {
                "source": "བྱང་ཆུབ་སེམས་ཀྱི་ལྗོན་ཤིང་རྟག་པར་ཡང་།",
                "translation": "The tree of awakening mind constantly produces fruit.",
                "sanskrit": "bodhicittadruma sadā",
                "glossary": self.glossaries[0],
                "combined_commentary": "The tree of bodhicitta is a metaphor for the mind of awakening.",
                "word_by_word_translation": "བྱང་ཆུབ་སེམས → awakening mind\nལྗོན་ཤིང → tree"
            }
        ]
        
        # Mock open function to prevent file writing
        with patch('builtins.open', MagicMock()):
            with patch('json.dump') as mock_json_dump:
                with patch('pandas.DataFrame.to_csv') as mock_to_csv:
                    # Run post-processing
                    result = post_process_corpus([self.corpus[0]], "test_output.json")
                    
                    # Verify calls
                    mock_analyze.assert_called_once()
                    mock_generate.assert_called_once()
                    mock_standardize.assert_called_once()
                    mock_apply.assert_called_once()
                    mock_wbw.assert_called_once()
                    mock_to_csv.assert_called_once()
                    mock_json_dump.assert_called_once()
                    
                    # Check result
                    self.assertEqual(result, mock_wbw.return_value)

if __name__ == '__main__':
    unittest.main()