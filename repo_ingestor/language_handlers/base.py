"""
Base language handler for detecting and processing language-specific files.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set, Dict, Any

from ..config import LanguageConfig


class BaseLanguageHandler(ABC):
    """Base class for language handlers."""

    def __init__(self, config: LanguageConfig):
        """
        Initialize the language handler.

        Args:
            config: Language configuration
        """
        self.config = config

    @abstractmethod
    def detect_language(self, repo_path: Path) -> bool:
        """
        Detect if this language is used in the repository.

        Args:
            repo_path: Path to the repository

        Returns:
            True if the language is detected, False otherwise
        """
        pass

    def get_include_patterns(self) -> Set[str]:
        """
        Get the patterns of files to include.

        Returns:
            Set of glob patterns for files to include
        """
        patterns = set()

        # Add file extensions
        for ext in self.config.extensions:
            patterns.add(f"*{ext}")

        # Add custom include patterns
        patterns.update(self.config.include_patterns)

        return patterns

    def get_exclude_patterns(self) -> Set[str]:
        """
        Get the patterns of files to exclude.

        Returns:
            Set of glob patterns for files to exclude
        """
        return self.config.exclude_patterns

    @abstractmethod
    def analyze_dependencies(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary mapping file paths to their dependencies
        """
        pass

    @abstractmethod
    def extract_project_metadata(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract project metadata from files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary with project metadata
        """
        pass