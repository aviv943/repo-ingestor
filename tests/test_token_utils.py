import unittest

from repo_ingestor.token_utils import estimate_tokens, estimate_repository_tokens


class TestTokenUtils(unittest.TestCase):

    def test_estimate_tokens(self):
        # Test with empty text
        self.assertEqual(estimate_tokens(""), 1)

        # Test with simple text
        text = "This is a simple text with some words."
        tokens = estimate_tokens(text)
        self.assertGreater(tokens, 0)

        # Test with code
        code = """
def test_function():
    result = 1 + 2
    print(f"The result is {result}")
    return result
"""
        code_tokens = estimate_tokens(code)
        self.assertGreater(code_tokens, 0)

        # Test with longer text should result in more tokens
        longer_text = text * 10
        longer_tokens = estimate_tokens(longer_text)
        self.assertGreater(longer_tokens, tokens)

    def test_estimate_repository_tokens(self):
        # Create a sample repository info dictionary
        repo_info = {
            'files': {
                'file1.py': 'def main():\n    print("Hello")',
                'file2.py': 'def another():\n    print("World")',
                'README.md': '# Sample\nThis is a sample repository.'
            },
            'metadata': {
                'languages': ['python'],
                'file_count': 3
            },
            'tree_structure': {
                'file1.py': None,
                'file2.py': None,
                'README.md': None
            },
            'file_dependencies': {
                'file1.py': [],
                'file2.py': []
            }
        }

        # Estimate tokens
        token_info = estimate_repository_tokens(repo_info)

        # Basic checks
        self.assertIn('total_tokens', token_info)
        self.assertIn('structure_tokens', token_info)
        self.assertIn('file_tokens', token_info)
        self.assertIn('top_files_by_tokens', token_info)
        self.assertIn('fits_in_models', token_info)
        self.assertIn('exceeds_models', token_info)

        # Verify token counts
        self.assertGreater(token_info['total_tokens'], 0)
        self.assertEqual(len(token_info['file_tokens']), 3)
        self.assertEqual(len(token_info['top_files_by_tokens']), 3)  # All 3 files should be in the top files

        # Check if fits_in_models or exceeds_models is populated correctly
        self.assertTrue(len(token_info['fits_in_models']) > 0 or len(token_info['exceeds_models']) > 0)


if __name__ == "__main__":
    unittest.main()