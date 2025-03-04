import os
import getpass

# API Configuration
os.environ["ANTHROPIC_API_KEY"] = getpass.getpass("Enter your API key")

# Model Configuration
LLM_MODEL_NAME = "claude-3-5-sonnet-latest"
MAX_TOKENS = 4000

# File Paths
GLOSSARY_CSV_PATH = "translation_glossary.csv"
STATE_JSONL_PATH = "translation_states.jsonl"

# Translation Settings
MAX_ITERATIONS = 6  # Maximum iterations before translation is accepted

# Formatting Settings
PRESERVE_SOURCE_FORMATTING = True  # Ensure translation matches source text formatting
