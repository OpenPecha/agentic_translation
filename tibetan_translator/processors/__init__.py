# __init__.py for tibetan_translator/processors package

from tibetan_translator.processors.commentary import *
from tibetan_translator.processors.translation import *
from tibetan_translator.processors.evaluation import *
from tibetan_translator.processors.formatting import *
from tibetan_translator.processors.glossary import *

__all__ = [
    "commentary",
    "translation",
    "evaluation",
    "formatting",
    "glossary"
]
