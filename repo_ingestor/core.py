import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

from .config import Config, DEFAULT_CONFIG
from .language_handlers import LANGUAGE_HANDLERS
from .utils import find_files, get_file_content, remove_comments_from_content
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
        Collect and read all relevant files from the repository.

        Args:
            repo_path: Path to the repository
            languages: List of languages to consider

        Returns:
            Dictionary mapping relative file paths to their content
        """
        include_patterns = set(self.config.common_include_patterns)
        exclude_patterns = set(self.config.common_exclude_patterns)

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
            self.config.max_file_size_kb
        )

        if self.progress:
            self.progress.update(self.task_id, description="Reading files...", advance=5)
            file_task = self.progress.add_task("Reading files...", total=len(file_paths))

        files = {}
        for file_path, relative_path in file_paths:
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

    def ingest(self, repo_path: str, token_estimate_only: bool = False) -> RepositoryInfo:
        """
        Analyze the complete repository and return structured information.

        Args:
            repo_path: Path to the repository directory

        Returns:
            RepositoryInfo object with complete analysis
        """
        repo_path = Path(repo_path).resolve()

        # Create a main task if using progress tracking
        if self.progress:
            self.task_id = self.progress.add_task("Analyzing repository...", total=100)

        languages = self._detect_languages(repo_path)
        files = self._collect_files(repo_path, languages)

        if token_estimate_only:
            if self.progress:
                self.progress.update(self.task_id, description="Estimating tokens...", advance=90)

            # Create minimal repo info for token estimation
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

        # Complete the progress bar
        if self.progress:
            self.progress.update(self.task_id,
                                 description="Analysis complete!",
                                 completed=100)

        # Return the complete repository information
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