import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

from .config import Config, DEFAULT_CONFIG
from .language_handlers import LANGUAGE_HANDLERS
from .utils import find_files, get_file_content, remove_comments_from_content, matches_any_pattern
from .token_utils import estimate_repository_tokens
from .function_analyzer import build_call_graph_from_files, analyze_non_python_functions

@dataclass
class RepositoryInfo:
    """Stores complete information about an analyzed repository."""
    root_path: Path
    languages: List[str]
    files: Dict[str, str]  # path -> content
    file_dependencies: Dict[str, List[str]]  # path -> list of dependencies
    metadata: Dict[str, Any]
    tree_structure: Dict[str, Any]
    token_info: Dict[str, Any]  # Token count information
    function_info: Dict[str, Any]  # Function call graph information

class RepositoryIngestor:
    """Analyzes repository content and structure."""

    def __init__(self, config: Config = None, progress_tracker=None):
        """
        Initialize the repository ingestor.

        Args:
            config: Configuration settings for analysis
            progress_tracker: Optional progress tracking object
        """
        self.config = config or DEFAULT_CONFIG
        self.handlers = {}
        self.progress = progress_tracker

    def _detect_languages(self, repo_path: Path) -> List[str]:
        """
        Detect programming languages used in the repository.

        Args:
            repo_path: Path to the repository

        Returns:
            List of detected language names
        """
        detected_languages = []

        if self.progress:
            self.progress.update(self.task_id, description="Detecting languages...", advance=5)

        for lang_name, handler_class in LANGUAGE_HANDLERS.items():
            handler = handler_class(self.config.languages.get(lang_name))
            if handler.detect_language(repo_path):
                detected_languages.append(lang_name)
                self.handlers[lang_name] = handler

        return detected_languages

    def _collect_files(self, repo_path: Path, languages: List[str]) -> Dict[str, str]:
        """
        Collect files for the specified languages from the repository

        Args:
            repo_path: Path to the repository
            languages: List of languages to collect files for

        Returns:
            Dictionary mapping file paths to file contents
        """
        include_patterns = set(self.config.common_include_patterns)
        exclude_patterns = set(self.config.common_exclude_patterns)

        # Only add language-specific patterns for the languages that are being analyzed
        for lang in languages:
            if lang in self.handlers:
                include_patterns.update(self.handlers[lang].get_include_patterns())
                exclude_patterns.update(self.handlers[lang].get_exclude_patterns())

        if self.progress:
            self.progress.update(self.task_id, description="Finding files...", advance=5)

        file_paths = find_files(
            repo_path,
            include_patterns,
            exclude_patterns,
            self.config.max_file_size_kb,
            self.config.max_depth
        )

        if self.progress:
            self.progress.update(self.task_id, description="Reading files...", advance=5)
            file_task = self.progress.add_task("Reading files...", total=len(file_paths))

        files = {}
        for file_path, relative_path in file_paths:
            # Check if the file should be included based on language
            should_include = False

            # If no languages filter specified, include all matched files
            if not languages:
                should_include = True
            else:
                # If the file matches a language-specific pattern, include it
                for lang in languages:
                    if lang in self.handlers:
                        lang_patterns = self.handlers[lang].get_include_patterns()
                        if any(matches_any_pattern(relative_path, {pattern}) for pattern in lang_patterns):
                            should_include = True
                            break

                # Still include files that match common include patterns like README.md
                # only if they explicitly match (not via wildcard)
                if not should_include:
                    explicit_common_patterns = {p for p in self.config.common_include_patterns
                                                if '*' not in p and '?' not in p}
                    if any(p == relative_path for p in explicit_common_patterns):
                        should_include = True

            # Skip files that don't match any language pattern
            if not should_include:
                continue

            content = get_file_content(file_path)

            if self.config.remove_comments:
                content = remove_comments_from_content(relative_path, content)

            files[relative_path] = content

            if self.progress:
                self.progress.update(file_task, advance=1)

        return files

    def _analyze_dependencies(self, files: Dict[str, str], languages: List[str]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between files in the repository.

        Args:
            files: Dictionary of file paths and their content
            languages: List of languages to analyze

        Returns:
            Dictionary mapping file paths to their dependencies
        """
        if self.progress:
            self.progress.update(self.task_id, description="Analyzing dependencies...", advance=10)

        all_dependencies = {}

        for lang in languages:
            if lang in self.handlers:
                lang_dependencies = self.handlers[lang].analyze_dependencies(files)
                all_dependencies.update(lang_dependencies)

        return all_dependencies

    def _extract_metadata(self, files: Dict[str, str], languages: List[str]) -> Dict[str, Any]:
        """
        Extract project metadata from the repository files.

        Args:
            files: Dictionary of file paths and their content
            languages: List of languages in the repository

        Returns:
            Dictionary containing repository metadata
        """
        if self.progress:
            self.progress.update(self.task_id, description="Extracting metadata...", advance=10)

        metadata = {
            "timestamp": time.time(),
            "languages": languages,
            "file_count": len(files),
            "language_metadata": {}
        }

        for lang in languages:
            if lang in self.handlers:
                lang_metadata = self.handlers[lang].extract_project_metadata(files)
                metadata["language_metadata"][lang] = lang_metadata

        return metadata

    def _build_tree_structure(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Build a hierarchical tree structure of the repository.

        Args:
            files: Dictionary of file paths and their content

        Returns:
            Nested dictionary representing the directory structure
        """
        if self.progress:
            self.progress.update(self.task_id, description="Building tree structure...", advance=10)

        tree = {}

        for file_path in files:
            parts = file_path.split(os.sep)
            current = tree

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # This is a file
                    current[part] = None
                else:
                    # This is a directory
                    if part not in current:
                        current[part] = {}
                    current = current[part]

        return tree

    def _analyze_tokens(self, files: Dict[str, str], metadata: Dict[str, Any],
                      tree: Dict[str, Any], dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Estimate token counts for the repository content.

        Args:
            files: Dictionary of file paths and their content
            metadata: Repository metadata
            tree: Repository directory structure
            dependencies: File dependencies

        Returns:
            Dictionary with token count information
        """
        if self.progress:
            self.progress.update(self.task_id, description="Estimating token counts...", advance=10)

        repo_data = {
            'files': files,
            'metadata': metadata,
            'tree_structure': tree,
            'file_dependencies': dependencies
        }

        return estimate_repository_tokens(repo_data)

    def _analyze_functions(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze function definitions and call graph in the repository.

        Args:
            files: Dictionary of file paths and their content

        Returns:
            Dictionary with function analysis information
        """
        if self.progress:
            self.progress.update(self.task_id, description="Analyzing function call graph...", advance=15)

        python_analysis = build_call_graph_from_files(files)
        other_analysis = analyze_non_python_functions(files)

        function_info = {
            **python_analysis,
            **other_analysis
        }

        python_func_count = len(python_analysis.get('functions', {}))
        other_func_count = other_analysis.get('function_count', 0)

        function_info['total_function_count'] = python_func_count + other_func_count
        function_info['analysis_coverage'] = {
            'python_functions': python_func_count,
            'other_functions': other_func_count,
            'python_files_analyzed': len(python_analysis.get('file_functions', {})),
            'other_files_analyzed': other_analysis.get('file_count', 0)
        }

        return function_info

    def ingest(self, repo_path: str, token_estimate_only: bool = False, languages_filter: List[str] = None) -> RepositoryInfo:
        """
        Ingest a repository and analyze its contents

        Args:
            repo_path: Path to the repository
            token_estimate_only: If True, only estimate tokens without full analysis
            languages_filter: List of language names to include (case-insensitive)

        Returns:
            RepositoryInfo object containing analysis results
        """
        repo_path = Path(repo_path).resolve()

        if self.progress:
            self.task_id = self.progress.add_task("Analyzing repository...", total=100)

        # Detect all available languages in the repository
        all_languages = self._detect_languages(repo_path)

        # Apply language filter if specified
        if languages_filter and all_languages:
            # Convert filters to lowercase for case-insensitive matching
            languages_filter_lower = [lang.lower() for lang in languages_filter]
            filtered_languages = [lang for lang in all_languages if lang.lower() in languages_filter_lower]
            languages = filtered_languages

            if self.progress and filtered_languages:
                self.progress.update(
                    self.task_id,
                    description=f"Analyzing {', '.join(filtered_languages)} files...",
                    advance=2
                )
            elif self.progress:
                self.progress.update(
                    self.task_id,
                    description="No matching languages found with specified filter!",
                    advance=2
                )
        else:
            languages = all_languages

        # Collect all files first
        files = self._collect_files(repo_path, all_languages)

        # If we have language filters, filter the files by extension
        if languages_filter and languages:
            filtered_files = {}

            # Get allowed extensions and config files for the filtered languages
            allowed_extensions = set()
            allowed_config_files = set()

            # Build whitelists from language configurations
            for lang in languages:
                if lang in self.config.languages:
                    lang_config = self.config.languages[lang]
                    allowed_extensions.update(lang_config.extensions)
                    allowed_config_files.update(lang_config.config_files)

            # Always allow certain core files like README
            allowed_core_files = {"README.md", "LICENSE"}

            # Filter the files
            for file_path, content in files.items():
                file_ext = os.path.splitext(file_path)[1].lower()
                file_name = os.path.basename(file_path)

                # Include if it's a core file
                if file_path in allowed_core_files or file_name in allowed_core_files:
                    filtered_files[file_path] = content
                # Include if it matches an allowed extension
                elif file_ext in allowed_extensions:
                    filtered_files[file_path] = content
                # Include if it matches an allowed config file pattern
                elif any(matches_any_pattern(file_path, {pattern}) for pattern in allowed_config_files):
                    filtered_files[file_path] = content

            # Replace the original files dictionary with the filtered one
            files = filtered_files

        if token_estimate_only:
            if self.progress:
                self.progress.update(self.task_id, description="Estimating tokens...", advance=90)

            dummy_tree = self._build_tree_structure(files)
            token_info = self._analyze_tokens(files, {"languages": languages}, dummy_tree, {})

            if self.progress:
                self.progress.update(self.task_id,
                                     description="Token estimation complete!",
                                     completed=100)

            return RepositoryInfo(
                root_path=repo_path,
                languages=languages,
                files=files,
                file_dependencies={},
                metadata={"languages": languages, "file_count": len(files)},
                tree_structure=dummy_tree,
                token_info=token_info,
                function_info={}
            )

        dependencies = self._analyze_dependencies(files, languages)
        metadata = self._extract_metadata(files, languages)
        tree = self._build_tree_structure(files)
        token_info = self._analyze_tokens(files, metadata, tree, dependencies)
        function_info = self._analyze_functions(files)

        if self.progress:
            self.progress.update(self.task_id,
                                 description="Analysis complete!",
                                 completed=100)

        return RepositoryInfo(
            root_path=repo_path,
            languages=languages,
            files=files,
            file_dependencies=dependencies,
            metadata=metadata,
            tree_structure=tree,
            token_info=token_info,
            function_info=function_info
        )