"""
Formatters for repository information output.
"""
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, TextIO, List

from .core import RepositoryInfo


class BaseFormatter(ABC):
    """Base class for formatters."""

    @abstractmethod
    def format(self, repo_info: RepositoryInfo, output_file: TextIO) -> None:
        """
        Format repository information and write to output file.

        Args:
            repo_info: Repository information
            output_file: Output file object
        """
        pass

class MarkdownFormatter(BaseFormatter):
    """Markdown formatter for repository information."""

    def _format_tree(self, tree: Dict[str, Any], indent: int = 0) -> str:
        """
        Format tree structure as Markdown.

        Args:
            tree: Tree structure
            indent: Indentation level

        Returns:
            Markdown formatted tree
        """
        result = []

        for name, subtree in sorted(tree.items()):
            # Files have None as their value
            if subtree is None:
                result.append(f"{' ' * indent}- 📄 `{name}`")
            else:
                result.append(f"{' ' * indent}- 📁 **{name}/**")
                result.append(self._format_tree(subtree, indent + 2))

        return "\n".join(result)

    def _format_dependencies(self, dependencies: Dict[str, Any]) -> str:
        """
        Format dependencies as Markdown.

        Args:
            dependencies: Dependencies dictionary

        Returns:
            Markdown formatted dependencies
        """
        result = []

        for file_path, deps in sorted(dependencies.items()):
            if deps:
                result.append(f"### `{file_path}`")
                for dep in sorted(deps):
                    result.append(f"- {dep}")
                result.append("")

        return "\n".join(result)

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata as Markdown.

        Args:
            metadata: Metadata dictionary

        Returns:
            Markdown formatted metadata
        """
        result = [
            f"## Repository Metadata",
            f"",
            f"- **Languages**: {', '.join(metadata.get('languages', []))}",
            f"- **File Count**: {metadata.get('file_count', 0)}",
            f""
        ]

        # Add language-specific metadata
        lang_metadata = metadata.get("language_metadata", {})
        for lang, lang_meta in lang_metadata.items():
            result.append(f"### {lang} Metadata")

            for key, value in lang_meta.items():
                if isinstance(value, list):
                    if value:
                        result.append(f"- **{key}**:")
                        for item in value:
                            if isinstance(item, dict):
                                item_str = ", ".join(f"{k}: {v}" for k, v in item.items())
                                result.append(f"  - {item_str}")
                            else:
                                result.append(f"  - {item}")
                else:
                    result.append(f"- **{key}**: {value}")

            result.append("")

        return "\n".join(result)

    def _format_token_info(self, token_info: Dict[str, Any]) -> str:
        """
        Format token count information as Markdown.

        Args:
            token_info: Token information dictionary

        Returns:
            Markdown formatted token information
        """
        result = [
            f"## Token Count Information",
            f"",
            f"- **Total Estimated Tokens**: {token_info.get('total_tokens', 0):,}",
            f"- **Structure Tokens**: {token_info.get('structure_tokens', 0):,}",
            f""
        ]

        # Add top files by token count
        top_files = token_info.get('top_files_by_tokens', [])
        if top_files:
            result.append(f"### Top Files by Token Count")
            result.append("")
            result.append("| File | Tokens |")
            result.append("| ---- | ------ |")

            for file_path, count in top_files:
                result.append(f"| `{file_path}` | {count:,} |")

            result.append("")

        return "\n".join(result)

    def _format_function_info(self, function_info: Dict[str, Any]) -> str:
        """
        Format function call information as Markdown.

        Args:
            function_info: Function information dictionary

        Returns:
            Markdown formatted function information
        """
        result = [
            f"## Function Call Graph",
            f"",
            f"- **Total Functions**: {function_info.get('total_function_count', 0)}",
            f""
        ]

        # Add highly connected functions
        highly_connected = function_info.get('highly_connected', [])
        if highly_connected:
            result.append(f"### Most Called Functions")
            result.append("")
            result.append("| Function | Called By |")
            result.append("| -------- | --------- |")

            for func, count in highly_connected:
                result.append(f"| `{func}` | {count} other functions |")

            result.append("")

        # Add function relationships
        functions = function_info.get('functions', {})
        if functions and len(functions) <= 30:  # Only show detailed relationships for smaller codebases
            result.append(f"### Function Relationships")
            result.append("")

            for func_name, func_data in sorted(functions.items()):
                calls = func_data.get('calls', [])
                called_by = func_data.get('called_by', [])

                if calls or called_by:
                    result.append(f"#### `{func_name}`")
                    result.append(f"- **Location**: {func_data.get('file_path', '')}:{func_data.get('start_line', '')}")

                    if calls:
                        result.append("- **Calls**:")
                        for called in sorted(calls):
                            result.append(f"  - `{called}`")

                    if called_by:
                        result.append("- **Called by**:")
                        for caller in sorted(called_by):
                            result.append(f"  - `{caller}`")

                    result.append("")

        return "\n".join(result)

    def format(self, repo_info: RepositoryInfo, output_file: TextIO) -> None:
        """
        Format repository information as Markdown and write to output file.

        Args:
            repo_info: Repository information
            output_file: Output file object
        """
        # Write header
        output_file.write(f"# Repository: {repo_info.root_path.name}\n\n")

        # Write token info (at the top for visibility)
        output_file.write(self._format_token_info(repo_info.token_info))
        output_file.write("\n\n")

        # Write function call graph
        output_file.write(self._format_function_info(repo_info.function_info))
        output_file.write("\n\n")

        # Write metadata
        output_file.write(self._format_metadata(repo_info.metadata))
        output_file.write("\n\n")

        # Write tree structure
        output_file.write("## Directory Structure\n\n")
        output_file.write(self._format_tree(repo_info.tree_structure))
        output_file.write("\n\n")

        # Write dependencies
        output_file.write("## File Dependencies\n\n")
        output_file.write(self._format_dependencies(repo_info.file_dependencies))
        output_file.write("\n\n")

        # Write file contents
        output_file.write("## File Contents\n\n")
        for file_path, content in sorted(repo_info.files.items()):
            ext = os.path.splitext(file_path)[1].lstrip(".")
            output_file.write(f"### {file_path}\n\n")
            output_file.write(f"```{ext}\n{content}\n```\n\n")


class TextFormatter(BaseFormatter):

    def _format_tree(self, tree: Dict[str, Any], prefix: str = "") -> str:

        result = []

        items = list(tree.items())
        for i, (name, subtree) in enumerate(sorted(items)):
            is_last = i == len(items) - 1

            if is_last:
                line_prefix = prefix + "└── "
                child_prefix = prefix + "    "
            else:
                line_prefix = prefix + "├── "
                child_prefix = prefix + "│   "

            if subtree is None:
                result.append(f"{line_prefix}{name}")
            else:
                result.append(f"{line_prefix}{name}/")
                result.append(self._format_tree(subtree, child_prefix))

        return "\n".join(result)

    def format(self, repo_info: RepositoryInfo, output_file: TextIO) -> None:

        output_file.write(f"Repository: {repo_info.root_path.name}\n")
        output_file.write("=" * (len(repo_info.root_path.name) + 12) + "\n\n")

        output_file.write("Token Count Information:\n")
        output_file.write("-" * 25 + "\n")
        output_file.write(f"Total Estimated Tokens: {repo_info.token_info.get('total_tokens', 0):,}\n")

        output_file.write("Function Analysis:\n")
        output_file.write("-" * 25 + "\n")
        output_file.write(f"Total Functions: {repo_info.function_info.get('total_function_count', 0)}\n")

        entry_points = repo_info.function_info.get('entry_points', [])
        if entry_points and len(entry_points) <= 5:
            output_file.write(f"Entry Points: {', '.join(entry_points)}\n")
        elif entry_points:
            output_file.write(f"Entry Points: {len(entry_points)} functions\n")

        output_file.write("\n")

        output_file.write(f"File count: {len(repo_info.files)}\n\n")

        output_file.write("Directory Structure:\n")
        output_file.write(self._format_tree(repo_info.tree_structure))
        output_file.write("\n\n")

        output_file.write("File Dependencies:\n")
        output_file.write("-" * 20 + "\n")
        for file_path, deps in sorted(repo_info.file_dependencies.items()):
            if deps:
                output_file.write(f"{file_path}:\n")
                for dep in sorted(deps):
                    output_file.write(f"  - {dep}\n")
                output_file.write("\n")

        file_extensions = {}
        for file_path in repo_info.files:
            ext = os.path.splitext(file_path)[1].lower()
            file_extensions[ext] = file_extensions.get(ext, 0) + 1

        output_file.write("File Extensions Summary:\n")
        for ext, count in sorted(file_extensions.items()):
            output_file.write(f"{ext or 'No extension'}: {count} files\n")

        # Add file contents section
        output_file.write("\nFile Contents:\n")
        output_file.write("=" * 20 + "\n\n")

        for file_path, content in sorted(repo_info.files.items()):
            output_file.write(f"File: {file_path}\n")
            output_file.write("-" * (len(file_path) + 6) + "\n")
            output_file.write(content)
            output_file.write("\n\n")

class JSONSummaryFormatter(BaseFormatter):
    """
    A formatter that produces a lightweight JSON output without including file contents.
    Useful for large repositories where the full JSON output would be too large.
    """
    def format(self, repo_info: RepositoryInfo, output_file: TextIO) -> None:
        data = {
            "languages": repo_info.languages,
            "file_count": len(repo_info.files),
            "metadata": repo_info.metadata,
            "tree_structure": repo_info.tree_structure,
            "dependencies": repo_info.file_dependencies,
            "token_info": repo_info.token_info,
            "function_info": repo_info.function_info,
            "file_list": sorted(list(repo_info.files.keys()))  # Just list the files without content
        }

        json.dump(data, output_file, indent=2, ensure_ascii=False)

# Map of format names to formatter classes
FORMATTERS = {
    "json": JSONSummaryFormatter,  # New lightweight option
    "markdown": MarkdownFormatter,
    "text": TextFormatter
}