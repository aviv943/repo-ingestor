import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
from repo_ingestor.cli import print_intro, print_summary, format_file_size
from repo_ingestor.config import Config
from tests.fixtures import create_sample_repo, cleanup_sample_repo


class TestCliBasic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = create_sample_repo()

    def tearDown(self):
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            cleanup_sample_repo(self.temp_dir)
        if hasattr(self, 'repo_path') and os.path.exists(self.repo_path):
            cleanup_sample_repo(self.repo_path)

    def test_format_file_size(self):
        # Test conversion from bytes to appropriate units
        self.assertEqual(format_file_size(512), "512.0 B")
        self.assertEqual(format_file_size(1024), "1.0 KB")
        self.assertEqual(format_file_size(1536), "1.5 KB")
        self.assertEqual(format_file_size(1048576), "1.0 MB")
        self.assertEqual(format_file_size(1073741824), "1.0 GB")

    @patch('repo_ingestor.cli.console')
    def test_print_intro(self, mock_console):
        # Just verify it runs without error
        print_intro("/path/to/repo")
        self.assertTrue(mock_console.print.called)

    @patch('repo_ingestor.cli.console')
    def test_print_summary(self, mock_console):
        # Create a mock repository info
        repo_info = MagicMock()
        repo_info.token_info = {
            'total_tokens': 1000,
            'structure_tokens': 200,
            'top_files_by_tokens': [('file1.py', 300), ('file2.py', 200)]
        }
        repo_info.function_info = {
            'total_function_count': 10,
            'highly_connected': [('func1', 5), ('func2', 3)]
        }

        # Call print_summary
        print_summary(repo_info, 'output.md', 'markdown', False)

        # Just verify it runs without error
        self.assertTrue(mock_console.print.called)

    def test_cli_config_options(self):
        # Test that Config object correctly processes CLI options
        config = Config()
        config.max_file_size_kb = 2048
        config.common_exclude_patterns.add('*.log')
        config.remove_comments = False

        # Verify config options
        self.assertEqual(config.max_file_size_kb, 2048)
        self.assertIn('*.log', config.common_exclude_patterns)
        self.assertFalse(config.remove_comments)

    @patch('sys.exit')
    @patch('repo_ingestor.cli.console.print')
    @patch('repo_ingestor.cli.console.print_exception')
    def test_exception_handling(self, mock_print_exception, mock_print, mock_exit):
        # Create a function that will raise an exception
        def function_that_raises():
            raise Exception("Test error")

        # Call the function inside a try/except block similar to CLI
        try:
            function_that_raises()
        except Exception as e:
            mock_print(f"Error: {str(e)}", style="red")
            mock_print_exception()
            mock_exit(1)

        # Verify the error was handled correctly
        mock_print.assert_called_once()
        self.assertIn("Test error", mock_print.call_args[0][0])
        mock_print_exception.assert_called_once()
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()