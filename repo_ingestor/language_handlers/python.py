"""
Python language handler.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any

from .base import BaseLanguageHandler
from ..config import LanguageConfig


class PythonLanguageHandler(BaseLanguageHandler):
    """Handler for Python language repositories."""

    def __init__(self, config: LanguageConfig = None):
        """
        Initialize the Python language handler.

        Args:
            config: Python language configuration (optional)
        """
        from ..config import DEFAULT_CONFIG
        super().__init__(config or DEFAULT_CONFIG.languages["python"])

    def detect_language(self, repo_path: Path) -> bool:
        """
        Detect if this repository uses Python.

        Args:
            repo_path: Path to the repository

        Returns:
            True if Python is detected, False otherwise
        """
        # Check for Python files
        py_files = list(repo_path.glob("**/*.py"))
        if py_files:
            return True

        # Check for Python configuration files
        for config_file in self.config.config_files:
            if list(repo_path.glob(f"**/{config_file}")):
                return True

        return False

    def analyze_dependencies(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between Python files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary mapping file paths to their dependencies
        """
        dependencies = {}

        for file_path, content in files.items():
            if not file_path.endswith(".py"):
                continue

            file_deps = []

            # Get imports
            import_matches = re.finditer(r'^(?:from\s+([\w.]+)\s+import\s+[\w,\s*]+|import\s+([\w.,\s]+))', content, re.MULTILINE)

            for match in import_matches:
                from_import = match.group(1)
                direct_import = match.group(2)

                module = from_import or direct_import
                if not module:
                    continue

                # Handle multiple imports (import os, sys, re)
                for mod in module.split(','):
                    mod = mod.strip()
                    if not mod:
                        continue

                    # Remove trailing alias (import numpy as np)
                    mod = re.sub(r'\s+as\s+\w+', '', mod)

                    # Add to dependencies
                    file_deps.append(mod)

            dependencies[file_path] = file_deps

        return dependencies

    def extract_project_metadata(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract Python project metadata from files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary with project metadata
        """
        metadata = {
            "language": "Python",
            "requirements": [],
            "entry_points": [],
            "packages": []
        }

        # Find requirements.txt
        for file_path, content in files.items():
            if os.path.basename(file_path) == "requirements.txt":
                requirements = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        requirements.append(line)
                metadata["requirements"] = requirements

            # Find setup.py
            elif os.path.basename(file_path) == "setup.py":
                # Extract packages
                packages_match = re.search(r'packages\s*=\s*\[([^\]]+)\]', content)
                if packages_match:
                    packages_str = packages_match.group(1)
                    packages = re.findall(r'[\'"]([^\'"]+)[\'"]', packages_str)
                    metadata["packages"].extend(packages)

                # Extract entry points
                entry_points_match = re.search(r'entry_points\s*=\s*{([^}]+)}', content)
                if entry_points_match:
                    entry_points_str = entry_points_match.group(1)
                    console_scripts_match = re.search(r'console_scripts[\'"]:\s*\[([^\]]+)\]', entry_points_str)
                    if console_scripts_match:
                        scripts_str = console_scripts_match.group(1)
                        scripts = re.findall(r'[\'"]([^\'"]+)[\'"]', scripts_str)
                        metadata["entry_points"].extend(scripts)

        return metadata