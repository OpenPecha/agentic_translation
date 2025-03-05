import json
from tibetan_translator.models import State
from langchain_anthropic import ChatAnthropic
import getpass
import os

# Initialize LLM instance
os.environ["ANTHROPIC_API_KEY"] = getpass.getpass("Enter your API key")
llm = ChatAnthropic(model="claude-3-5-sonnet-latest", max_tokens=4000)

def dict_to_text(d, indent=0):
    """Convert dictionary to formatted text."""
    text = ""
    spacing = " " * indent
    
    for key, value in d.items():
        if isinstance(value, dict):
            text += f"{spacing}{key}:\n{dict_to_text(value, indent + 2)}"
        else:
            text += f"{spacing}{key}: {value}\n"
    
    return text

def convert_state_to_jsonl(state_dict: State, file_path: str):
    """Save the state dictionary in JSONL format."""
    with open(file_path, 'a', encoding='utf-8') as f:
        json.dump(state_dict, f, ensure_ascii=False)
        f.write("\n")
def get_json_data(file_path='commentary_1.json'):
    """Load data from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data
