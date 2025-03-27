# Tibetan Text Translation with Google Gemini API

This project contains two Python scripts for translating Tibetan Buddhist texts using Google's Gemini API:

1. `simple_translate.py` - Translates only the commentary fields in JSON files
2. `simple_translate_full.py` - Can translate both root text and commentary fields with options

## Prerequisites

1. Install the Google Gemini API client:
   ```
   pip install google-genai
   ```

2. Get a Google API key:
   - Go to https://ai.google.dev/
   - Sign up for Gemini API access
   - Generate an API key

3. Set your API key using one of these methods:

   **Option A: Environment variable**
   ```
   export GOOGLE_API_KEY="your-api-key-here"
   ```
   
   **Option B: .env file**
   Create a file named `.env` in the same directory as the scripts:
   ```
   GOOGLE_API_KEY=your-api-key-here
   ```
   
   Then install the dotenv package:
   ```
   pip install python-dotenv
   ```

## File Format

The scripts expect JSON files with the following structure:

```json
[
  {
    "root": "བཅོམ་ལྡན་འདས་མ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པའི་སྙིང་པོ། །",
    "commentary": "འདི་སྐད་བདག་གིས་ཐོས་པ་དུས་གཅིག་ན་ཞེས་པ་འདི་ནི་དུས་གཞན་དུ་མ་ཡིན་ཏེ།"
  },
  {
    "root": "...",
    "commentary": "..."
  }
]
```

Or a single object with the same structure:

```json
{
  "root": "བཅོམ་ལྡན་འདས་མ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པའི་སྙིང་པོ། །",
  "commentary": "འདི་སྐད་བདག་གིས་ཐོས་པ་དུས་གཅིག་ན་ཞེས་པ་འདི་ནི་དུས་གཞན་དུ་མ་ཡིན་ཏེ།"
}
```

## Usage

### Simple Translation Script (Commentary Only)

This script translates only the commentary fields and supports parallel processing of multiple files:

```
# Process a single file (translate to English)
python simple_translate.py input.json

# Process multiple files simultaneously
python simple_translate.py input1.json input2.json input3.json

# Use glob pattern to process all JSON files in the current directory
python simple_translate.py *.json

# Translate to a different language
python simple_translate.py input.json --target-lang Spanish

# Control the number of parallel worker threads
python simple_translate.py *.json --max-workers 5 --target-lang Chinese
```

The output filenames are auto-generated based on the input filenames and target language:
- `input.json` → `input_translated_english.json`
- `input.json` with Spanish → `input_translated_spanish.json`

The output file will have the same structure as the input, with an additional field (e.g., `commentary_english`, `commentary_spanish`, etc.) containing the translation.

### Full Translation Script (Commentary and/or Root)

This script can translate both root text and commentary fields and supports parallel processing of multiple files:

```
# Default: translate only commentary fields to English
python simple_translate_full.py input.json

# Process multiple files simultaneously
python simple_translate_full.py input1.json input2.json input3.json

# Use glob pattern to process all JSON files in the current directory
python simple_translate_full.py *.json

# Translate only root text fields
python simple_translate_full.py input.json --root-only

# Translate both root and commentary fields
python simple_translate_full.py input.json --root-only --commentary-only

# Translate to a different language
python simple_translate_full.py input.json --target-lang Spanish

# Process multiple files with specific settings
python simple_translate_full.py *.json --root-only --target-lang Chinese --max-workers 5
```

The output filenames are auto-generated based on the input filenames, translation type, and target language:
- `input.json` (commentary only) → `input_translated_commentary_english.json`
- `input.json` (root only) → `input_translated_root_english.json`
- `input.json` (both) → `input_translated_full_english.json`

The output file will have additional fields (e.g., `commentary_english`, `root_english`, `commentary_spanish`, etc.) containing the translations.

## Example

For the test file `test_simple_translate.json`:

```
python simple_translate.py test_simple_translate.json test_simple_translate_out.json
```

## Notes

1. The scripts maintain empty fields as empty (they don't try to translate empty strings)
2. Large texts may exceed token limits - consider breaking them into smaller chunks if needed
3. Translation quality depends on the Gemini model and may require manual review
4. The API calls cost money depending on your Google Gemini API pricing plan

## Customization

You can modify the translation prompt in the scripts to adjust the style and accuracy of translations:

```python
TRANSLATION_PROMPT = """
You are a Tibetan Buddhist scholar and translator with expertise in translating Tibetan Buddhist texts.
Translate the following Tibetan text into clear, accurate English.
Maintain the philosophical and technical Buddhist terminology accurately.
Translate with sensitivity to the context of Tibetan Buddhist philosophy.

Tibetan text:
{text}

Translate the above Tibetan text into English:
"""
```

You can also adjust the generation parameters in the `translate_text` function:

```python
config={
    "temperature": 0.2,  # Lower for more deterministic outputs
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 4096,  # Adjust based on expected output length
}
```