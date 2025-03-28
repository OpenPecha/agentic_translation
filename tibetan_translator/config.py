import os
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
try:
    load_dotenv()
except ImportError:
    print("python-dotenv module not found. Please install: pip install python-dotenv")
    sys.exit(1)

# API Configuration
# Get API keys from environment variables (.env file)
if "ANTHROPIC_API_KEY" not in os.environ:
    print("Error: ANTHROPIC_API_KEY not found in environment variables.")
    print("Make sure you have a .env file with your API key.")
    sys.exit(1)

# Model Configuration
LLM_MODEL_NAME = "claude-3-7-sonnet-latest"
MAX_TOKENS = 5000

# File Paths
GLOSSARY_CSV_PATH = "translation_glossary.csv"
STATE_JSONL_PATH = "translation_states.jsonl"

# Translation Settings
MAX_TRANSLATION_ITERATIONS = 3 # Maximum iterations for translation quality improvements

# Formatting Settings
PRESERVE_SOURCE_FORMATTING = True  # Ensure translation matches source text formatting
MAX_FORMAT_ITERATIONS = 1  # Maximum iterations for formatting corrections