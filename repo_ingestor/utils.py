"""
Utility functions for the repository ingestor.
"""
import os
import re
import fnmatch
from pathlib import Path
from typing import List, Set, Tuple


def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file is binary, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Try to read as text
        return False
    except UnicodeDecodeError:
        return True


def matches_any_pattern(path: str, patterns: Set[str]) -> bool:
    """
    Check if a path matches any of the given patterns.

    Args:
        path: The path to check
        patterns: Set of patterns to match against

    Returns:
        True if the path matches any pattern, False otherwise
    """
    # Normalize path to use forward slashes for consistent matching
    normalized_path = path.replace('\\', '/')

    # Also create a version without leading dot for matching paths that might appear differently
    no_dot_path = normalized_path
    if normalized_path.startswith('./'):
        no_dot_path = normalized_path[2:]

    for pattern in patterns:
        pattern = pattern.replace('\\', '/')

        # Handle directory exclusions - match if pattern is a directory prefix
        if pattern.endswith('/'):
            dir_pattern = pattern[:-1]
            if (normalized_path.startswith(dir_pattern + '/') or
                    normalized_path == dir_pattern or
                    no_dot_path.startswith(dir_pattern + '/') or
                    no_dot_path == dir_pattern):
                return True

        # Handle dot-prefixed directories - match with or without the dot
        if pattern.startswith('.'):
            no_dot_pattern = pattern[1:]
            if (fnmatch.fnmatch(normalized_path, no_dot_pattern) or
                    fnmatch.fnmatch(normalized_path, '*/' + no_dot_pattern) or
                    fnmatch.fnmatch(normalized_path, no_dot_pattern + '/*')):
                return True

        # Standard pattern matching
        if fnmatch.fnmatch(normalized_path, pattern):
            return True

        # Also try matching against parts of the path for directory-based patterns
        path_parts = normalized_path.split('/')
        for i in range(len(path_parts)):
            partial_path = '/'.join(path_parts[i:])
            if fnmatch.fnmatch(partial_path, pattern):
                return True

    return False

def find_files(
        root_dir: Path,
        include_patterns: Set[str],
        exclude_patterns: Set[str],
        max_size_kb: int,
        max_depth: int = None
) -> List[Tuple[Path, str]]:
    result = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        if max_depth is not None:
            rel_dirpath = os.path.relpath(dirpath, root_dir)
            current_depth = 0 if rel_dirpath == '.' else len(rel_dirpath.split(os.sep))
            if current_depth >= max_depth:
                dirnames.clear()  # Don't go deeper

        # Convert to relative path for pattern matching
        rel_dirpath = os.path.relpath(dirpath, root_dir)

        # Process subdirectories
        i = 0
        while i < len(dirnames):
            # Get the relative directory path for this subdirectory
            rel_subdir = os.path.join(rel_dirpath, dirnames[i])
            if rel_subdir == '.':
                rel_subdir = dirnames[i]

            # If this directory matches exclusion pattern, remove it to skip traversal
            if matches_any_pattern(rel_subdir, exclude_patterns):
                dirnames.pop(i)
            else:
                i += 1

        # Process files
        for filename in filenames:
            file_path = Path(os.path.join(dirpath, filename))
            relative_path = str(file_path.relative_to(root_dir))

            # Skip excluded files
            if matches_any_pattern(relative_path, exclude_patterns):
                continue

            # Skip large files
            if file_path.stat().st_size > max_size_kb * 1024:
                continue

            # Include files matching include patterns
            if matches_any_pattern(relative_path, include_patterns):
                if not is_binary_file(file_path):
                    result.append((file_path, relative_path))

    return result


def get_file_content(file_path: Path) -> str:
    """
    Get the content of a file as a string.

    Args:
        file_path: Path to the file

    Returns:
        Content of the file as a string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to reading as binary and decoding with errors ignored
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='replace')


def remove_comments_from_content(file_path: str, content: str) -> str:
    """
    Remove comments from file content based on file extension.

    Args:
        file_path: Path to the file
        content: Content of the file

    Returns:
        Content with comments removed
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.py':
        # Remove Python comments
        # First, handle docstrings (triple quotes)
        content = re.sub(r'"""[\s\S]*?"""', '', content)
        content = re.sub(r"'''[\s\S]*?'''", '', content)
        # Then, handle line comments
        content = re.sub(r'^\s*#.*$', '', content, flags=re.MULTILINE)

    elif ext in ['.js', '.jsx', '.ts', '.tsx', '.cs', '.java', '.c', '.cpp', '.h', '.hpp']:
        # Remove C-style comments
        # First, handle block comments
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        # Then, handle line comments
        content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)

    elif ext in ['.html', '.xml', '.csproj', '.sln']:
        # Remove HTML/XML comments
        content = re.sub(r'<!--[\s\S]*?-->', '', content)

    elif ext == '.css':
        # Remove CSS comments
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)

    # Remove empty lines that may result from comment removal
    content = re.sub(r'\n\s*\n', '\n\n', content)

    return content


def get_dependencies_from_file(file_path: Path, file_content: str = None) -> List[str]:
    """
    Extract dependencies from a file based on its extension.
    This is a simplified version and would need enhancement for real use.

    Args:
        file_path: Path to the file
        file_content: Content of the file (optional)

    Returns:
        List of dependencies
    """
    ext = file_path.suffix.lower()

    if file_content is None:
        file_content = get_file_content(file_path)

    dependencies = []

    if ext == '.py':
        # Simple regex for Python imports
        import re
        imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)', file_content, re.MULTILINE)
        for imp in imports:
            module = imp[0] or imp[1]
            if module and module not in dependencies:
                dependencies.append(module)

    elif ext in ('.js', '.jsx', '.ts', '.tsx'):
        # Simple regex for JavaScript/TypeScript imports
        import re
        imports = re.findall(r'(?:import|require)\s*\(?[\'"]([^\'")]+)[\'"]', file_content)
        for imp in imports:
            if imp and imp not in dependencies:
                dependencies.append(imp)

    elif ext == '.csproj':
        # Simple regex for C# project references
        import re
        imports = re.findall(r'<PackageReference\s+Include="([^"]+)"', file_content)
        for imp in imports:
            if imp and imp not in dependencies:
                dependencies.append(imp)

    return dependencies