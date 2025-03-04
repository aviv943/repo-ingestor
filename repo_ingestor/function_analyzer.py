"""
Function call graph analysis for repository files.
"""
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional


class FunctionInfo:
    """Information about a function in a file."""

    def __init__(self, name: str, file_path: str, start_line: int, end_line: int):
        """
        Initialize function information.

        Args:
            name: Function name
            file_path: Path to the file containing the function
            start_line: Starting line number of the function
            end_line: Ending line number of the function
        """
        self.name = name
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.calls: List[str] = []
        self.called_by: List[str] = []

    def __str__(self) -> str:
        """String representation of the function information."""
        return f"{self.name} ({self.file_path}:{self.start_line}-{self.end_line})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'file_path': self.file_path,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'calls': self.calls,
            'called_by': self.called_by
        }


class PythonFunctionCallAnalyzer(ast.NodeVisitor):
    """AST-based analyzer for Python function calls."""

    def __init__(self, file_path: str):
        """
        Initialize Python function call analyzer.

        Args:
            file_path: Path to the Python file
        """
        self.file_path = file_path
        self.functions: Dict[str, FunctionInfo] = {}
        self.current_function: Optional[FunctionInfo] = None
        self.function_calls: Dict[str, List[str]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Visit function definition nodes.

        Args:
            node: Function definition AST node
        """
        function_name = node.name
        full_name = function_name  # For global functions
        if hasattr(node, 'parent_class'):
            full_name = f"{node.parent_class}.{function_name}"

        func_info = FunctionInfo(
            full_name,
            self.file_path,
            node.lineno,
            node.end_lineno or node.lineno
        )
        self.functions[full_name] = func_info

        # Track current function for nested calls
        old_function = self.current_function
        self.current_function = func_info

        # Visit function body
        for child in ast.iter_child_nodes(node):
            self.visit(child)

        # Restore previous function context
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visit class definition nodes.

        Args:
            node: Class definition AST node
        """
        class_name = node.name

        # Add class name to methods for proper identification
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                child.parent_class = class_name

        # Visit all class contents
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def visit_Call(self, node: ast.Call) -> None:
        """
        Visit function call nodes.

        Args:
            node: Function call AST node
        """
        if self.current_function:
            # Extract the name of the called function
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    # Method call like obj.method()
                    func_name = f"{node.func.value.id}.{node.func.attr}"
                else:
                    # Just use method name as fallback
                    func_name = node.func.attr

            if func_name:
                if func_name not in self.current_function.calls:
                    self.current_function.calls.append(func_name)

        # Continue visiting children
        for child in ast.iter_child_nodes(node):
            self.visit(child)


def build_call_graph_from_files(files: Dict[str, str]) -> Dict[str, Any]:
    """
    Build a function call graph from repository files.

    Args:
        files: Dictionary mapping file paths to their content

    Returns:
        Dictionary with function call graph information
    """
    all_functions: Dict[str, FunctionInfo] = {}
    file_functions: Dict[str, List[str]] = {}

    # First pass: Extract all functions and their direct calls
    for file_path, content in files.items():
        # For now, only analyze Python files
        if not file_path.endswith('.py'):
            continue

        file_functions[file_path] = []

        try:
            # Parse Python code into AST
            tree = ast.parse(content)
            analyzer = PythonFunctionCallAnalyzer(file_path)
            analyzer.visit(tree)

            # Add discovered functions
            for func_name, func_info in analyzer.functions.items():
                all_functions[func_name] = func_info
                file_functions[file_path].append(func_name)
        except SyntaxError:
            # Skip files with syntax errors
            continue

    # Second pass: Map function relationships (called_by)
    for caller_name, caller_info in all_functions.items():
        for called_func in caller_info.calls:
            if called_func in all_functions:
                if caller_name not in all_functions[called_func].called_by:
                    all_functions[called_func].called_by.append(caller_name)

    # Create entry points list (functions not called by others)
    entry_points = [
        name for name, info in all_functions.items()
        if not info.called_by and info.calls  # No callers and has calls
    ]

    # Create highly connected functions list (called by many)
    highly_connected = sorted(
        [(name, len(info.called_by)) for name, info in all_functions.items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]  # Top 10 most called functions

    return {
        'functions': {name: info.to_dict() for name, info in all_functions.items()},
        'file_functions': file_functions,
        'entry_points': entry_points,
        'highly_connected': highly_connected
    }


def analyze_non_python_functions(files: Dict[str, str]) -> Dict[str, Any]:
    """
    Use regex-based approach to extract function information from non-Python files.
    This is less accurate but provides basic function detection.

    Args:
        files: Dictionary mapping file paths to their content

    Returns:
        Dictionary with basic function information
    """
    function_patterns = {
        # JavaScript/TypeScript function patterns
        '.js': [
            r'function\s+([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{',  # Regular functions
            r'(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?:=>|{)',  # Arrow functions
            r'(?:class|interface)\s+([A-Za-z0-9_$]+)'  # Classes/interfaces
        ],
        '.jsx': [
            r'function\s+([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{',
            r'(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?:=>|{)',
            r'(?:class|interface)\s+([A-Za-z0-9_$]+)'
        ],
        '.ts': [
            r'function\s+([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{',
            r'(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?:=>|{)',
            r'(?:class|interface)\s+([A-Za-z0-9_$]+)'
        ],
        '.tsx': [
            r'function\s+([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{',
            r'(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?:=>|{)',
            r'(?:class|interface)\s+([A-Za-z0-9_$]+)'
        ],
        # C# patterns
        '.cs': [
            r'(?:public|private|protected|internal|static)*\s+(?:async\s+)?[A-Za-z0-9_<>]+\s+([A-Za-z0-9_]+)\s*\([^)]*\)',  # Methods
            r'(?:class|interface|struct|enum)\s+([A-Za-z0-9_]+)'  # Classes/interfaces
        ],
    }

    results = {}

    for file_path, content in files.items():
        ext = Path(file_path).suffix.lower()
        if ext not in function_patterns:
            continue

        functions = []
        for pattern in function_patterns[ext]:
            matches = re.findall(pattern, content)
            functions.extend(matches)

        if functions:
            results[file_path] = list(set(functions))  # Remove duplicates

    return {
        'regex_detected_functions': results,
        'file_count': len(results),
        'function_count': sum(len(funcs) for funcs in results.values())
    }