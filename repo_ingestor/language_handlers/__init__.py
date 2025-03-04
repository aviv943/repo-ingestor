"""
Language handlers package.
"""
from .base import BaseLanguageHandler
from .csharp import CSharpLanguageHandler
from .python import PythonLanguageHandler
from .react import ReactLanguageHandler

__all__ = [
    'BaseLanguageHandler',
    'CSharpLanguageHandler',
    'PythonLanguageHandler',
    'ReactLanguageHandler',
]

# Map of language names to handler classes
LANGUAGE_HANDLERS = {
    'csharp': CSharpLanguageHandler,
    'python': PythonLanguageHandler,
    'react': ReactLanguageHandler,
}