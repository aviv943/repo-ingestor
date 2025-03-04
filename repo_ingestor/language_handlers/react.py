"""
React language handler.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any

from .base import BaseLanguageHandler
from ..config import LanguageConfig


class ReactLanguageHandler(BaseLanguageHandler):
    """Handler for React language repositories."""

    def __init__(self, config: LanguageConfig = None):
        """
        Initialize the React language handler.

        Args:
            config: React language configuration (optional)
        """
        from ..config import DEFAULT_CONFIG
        super().__init__(config or DEFAULT_CONFIG.languages["react"])

    def detect_language(self, repo_path: Path) -> bool:
        """
        Detect if this repository uses React.

        Args:
            repo_path: Path to the repository

        Returns:
            True if React is detected, False otherwise
        """
        # Check for React-specific files
        jsx_files = list(repo_path.glob("**/*.jsx")) + list(repo_path.glob("**/*.tsx"))
        if jsx_files:
            return True

        # Check for package.json with React dependency
        package_json_files = list(repo_path.glob("**/package.json"))
        for package_file in package_json_files:
            try:
                with open(package_file, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    dependencies = package_data.get('dependencies', {})
                    if 'react' in dependencies:
                        return True
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

        return False

    def analyze_dependencies(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between React files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary mapping file paths to their dependencies
        """
        dependencies = {}

        for file_path, content in files.items():
            if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                file_deps = []

                # Get import statements
                import_matches = re.findall(r'(?:import|require)\s*\(?[\'"]([^\'")]+)[\'"]', content)
                file_deps.extend(import_matches)

                dependencies[file_path] = file_deps

            elif os.path.basename(file_path) == "package.json":
                try:
                    package_data = json.loads(content)
                    file_deps = []

                    # Get dependencies from package.json
                    deps = package_data.get('dependencies', {})
                    for dep_name in deps:
                        file_deps.append(dep_name)

                    # Get dev dependencies
                    dev_deps = package_data.get('devDependencies', {})
                    for dep_name in dev_deps:
                        file_deps.append(dep_name)

                    dependencies[file_path] = file_deps
                except json.JSONDecodeError:
                    dependencies[file_path] = []

        return dependencies

    def extract_project_metadata(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract React project metadata from files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary with project metadata
        """
        metadata = {
            "language": "React",
            "dependencies": [],
            "devDependencies": [],
            "scripts": []
        }

        for file_path, content in files.items():
            if os.path.basename(file_path) == "package.json":
                try:
                    package_data = json.loads(content)

                    # Get dependencies
                    deps = package_data.get('dependencies', {})
                    for dep_name, dep_version in deps.items():
                        metadata["dependencies"].append({
                            "name": dep_name,
                            "version": dep_version
                        })

                    # Get dev dependencies
                    dev_deps = package_data.get('devDependencies', {})
                    for dep_name, dep_version in dev_deps.items():
                        metadata["devDependencies"].append({
                            "name": dep_name,
                            "version": dep_version
                        })

                    # Get scripts
                    scripts = package_data.get('scripts', {})
                    for script_name, script_command in scripts.items():
                        metadata["scripts"].append({
                            "name": script_name,
                            "command": script_command
                        })

                    # Get other metadata
                    for key in ["name", "version", "description", "author", "license"]:
                        if key in package_data:
                            metadata[key] = package_data[key]

                except json.JSONDecodeError:
                    pass

        return metadata