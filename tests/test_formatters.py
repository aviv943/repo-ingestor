import unittest
import io
import json
import tempfile
from pathlib import Path

from repo_ingestor.formatters import (
    BaseFormatter,
    JSONSummaryFormatter,
    MarkdownFormatter,
    TextFormatter,
    FORMATTERS
)
from repo_ingestor.core import RepositoryInfo


class TestFormatters(unittest.TestCase):

    def setUp(self):
        # Create a sample repository info object for testing
        self.repo_info = RepositoryInfo(
            root_path=Path("/sample/repo"),
            languages=["python", "csharp"],
            files={
                "main.py": "def main():\n    print('Hello')",
                "utils.py": "def helper():\n    return 'Helper'",
                "Program.cs": "class Program\n{\n    static void Main(){}\n}"
            },
            file_dependencies={
                "main.py": ["utils.py"],
                "utils.py": []
            },
            metadata={
                "languages": ["python", "csharp"],
                "file_count": 3,
                "language_metadata": {
                    "python": {
                        "requirements": ["pytest", "click"],
                        "entry_points": ["sample=main:main"]
                    },
                    "csharp": {
                        "projects": ["Sample.csproj"]
                    }
                }
            },
            tree_structure={
                "main.py": None,
                "utils.py": None,
                "Program.cs": None
            },
            token_info={
                "total_tokens": 500,
                "structure_tokens": 100,
                "file_tokens": {
                    "main.py": 150,
                    "utils.py": 120,
                    "Program.cs": 130
                },
                "top_files_by_tokens": [
                    ("main.py", 150),
                    ("Program.cs", 130),
                    ("utils.py", 120)
                ]
            },
            function_info={
                "total_function_count": 3,
                "functions": {
                    "main": {
                        "name": "main",
                        "file_path": "main.py",
                        "start_line": 1,
                        "end_line": 2,
                        "calls": ["helper"],
                        "called_by": []
                    },
                    "helper": {
                        "name": "helper",
                        "file_path": "utils.py",
                        "start_line": 1,
                        "end_line": 2,
                        "calls": [],
                        "called_by": ["main"]
                    }
                },
                "highly_connected": [
                    ("helper", 1),
                    ("main", 0)
                ]
            }
        )

    def test_markdown_formatter(self):
        # Create a formatter
        formatter = MarkdownFormatter()

        # Create a buffer to write the output
        output = io.StringIO()

        # Format the repository info
        formatter.format(self.repo_info, output)

        # Get the output
        output_str = output.getvalue()

        # Verify markdown structure contains expected sections
        self.assertIn("# Repository:", output_str)
        self.assertIn("## Token Count Information", output_str)
        self.assertIn("## Function Call Graph", output_str)
        self.assertIn("## Repository Metadata", output_str)
        self.assertIn("## Directory Structure", output_str)
        self.assertIn("## File Dependencies", output_str)
        self.assertIn("## File Contents", output_str)

        # Verify some specific content
        self.assertIn("**Total Estimated Tokens**: 500", output_str)
        self.assertIn("**Total Functions**: 3", output_str)
        self.assertIn("main.py", output_str)
        self.assertIn("utils.py", output_str)
        self.assertIn("Program.cs", output_str)

    def test_text_formatter(self):
        # Create a formatter
        formatter = TextFormatter()

        # Create a buffer to write the output
        output = io.StringIO()

        # Format the repository info
        formatter.format(self.repo_info, output)

        # Get the output
        output_str = output.getvalue()

        # Verify text structure contains expected sections
        self.assertIn("Repository:", output_str)
        self.assertIn("Token Count Information:", output_str)
        self.assertIn("Function Analysis:", output_str)
        self.assertIn("Directory Structure:", output_str)
        self.assertIn("File Dependencies:", output_str)
        self.assertIn("File Extensions Summary:", output_str)
        self.assertIn("File Contents:", output_str)

        # Verify some specific content
        self.assertIn("Total Estimated Tokens: 500", output_str)
        self.assertIn("Total Functions: 3", output_str)
        self.assertIn("main.py", output_str)
        self.assertIn("utils.py", output_str)
        self.assertIn("Program.cs", output_str)

    def test_formatters_map(self):
        # Verify all expected formatters are available
        self.assertIn("json", FORMATTERS)
        self.assertIn("markdown", FORMATTERS)
        self.assertIn("text", FORMATTERS)

        # Verify formatter classes
        self.assertEqual(FORMATTERS["markdown"], MarkdownFormatter)
        self.assertEqual(FORMATTERS["text"], TextFormatter)


if __name__ == "__main__":
    unittest.main()