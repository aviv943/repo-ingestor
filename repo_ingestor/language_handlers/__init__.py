from .base import BaseLanguageHandler
from .csharp import CSharpLanguageHandler
from .python import PythonLanguageHandler
from .react import ReactLanguageHandler
from .yaml import YamlLanguageHandler

__all__ = [
    'BaseLanguageHandler',
    'CSharpLanguageHandler',
    'PythonLanguageHandler',
    'ReactLanguageHandler',
    'YamlLanguageHandler',
]

LANGUAGE_HANDLERS = {
    'csharp': CSharpLanguageHandler,
    'python': PythonLanguageHandler,
    'react': ReactLanguageHandler,
    'yaml': YamlLanguageHandler,
}