# Tibetan Translator Project Guide

## Commands
- Run tests: `python -m pytest tests/`
- Run single test: `python -m pytest tests/test_workflow.py::test_function_name -v`
- Run workflow: `python test_workflow.py`
- Batch process: `python batch_process.py`
- Example run: `python examples/basic_usage.py`

## Code Style Guidelines
- **Typing**: Use type hints consistently; Pydantic models for structured I/O
- **Imports**: Use absolute imports; import specific functions rather than modules
- **Naming**: 
  - snake_case for functions, variables, and modules
  - CamelCase for classes and Pydantic models
- **Error Handling**: Use try/except blocks with specific error types; avoid bare exceptions
- **Documentation**: Document functions with docstrings explaining parameters and return values
- **Structure**: Keep LangGraph nodes as pure functions with explicit inputs/outputs
- **Formatting**: 4 spaces for indentation; 100 character line limit

Use langgraph for workflow management and follow the existing pattern of processor modules for adding new functionality.