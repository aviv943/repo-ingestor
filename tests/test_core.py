import unittest
import os
import tempfile
from pathlib import Path

from repo_ingestor.core import RepositoryInfo, RepositoryIngestor
from repo_ingestor.config import Config
from repo_ingestor.utils import matches_any_pattern

from tests.fixtures import create_sample_repo, cleanup_sample_repo


class TestRepositoryInfo(unittest.TestCase):

    def test_repository_info_creation(self):
        # Create a RepositoryInfo object
        repo_info = RepositoryInfo(
            root_path=Path("/test/path"),
            languages=["python", "csharp"],
            files={"file1.py": "content1", "file2.cs": "content2"},
            file_dependencies={"file1.py": ["dep1"], "file2.cs": ["dep2"]},
            metadata={"key": "value"},
            tree_structure={"file1.py": None, "file2.cs": None},
            token_info={"total_tokens": 100},
            function_info={"total_functions": 5}
        )

        # Verify attributes
        self.assertEqual(repo_info.root_path, Path("/test/path"))
        self.assertEqual(repo_info.languages, ["python", "csharp"])
        self.assertEqual(repo_info.files, {"file1.py": "content1", "file2.cs": "content2"})
        self.assertEqual(repo_info.file_dependencies, {"file1.py": ["dep1"], "file2.cs": ["dep2"]})
        self.assertEqual(repo_info.metadata, {"key": "value"})
        self.assertEqual(repo_info.tree_structure, {"file1.py": None, "file2.cs": None})
        self.assertEqual(repo_info.token_info, {"total_tokens": 100})
        self.assertEqual(repo_info.function_info, {"total_functions": 5})


class TestRepositoryIngestor(unittest.TestCase):

    def setUp(self):
        # Create a config for testing
        self.config = Config()

        # Create a repository ingestor
        self.ingestor = RepositoryIngestor(self.config)

    def test_detect_languages(self):
        # Create a sample repository
        repo_path = create_sample_repo()

        # Detect languages (accessing a protected method for testing)
        languages = self.ingestor._detect_languages(Path(repo_path))

        # Verify detected languages
        self.assertIn("python", languages)
        self.assertIn("csharp", languages)
        self.assertIn("react", languages)

        # Clean up
        cleanup_sample_repo(repo_path)

    def test_collect_files(self):
        # Create a sample repository
        repo_path = create_sample_repo()

        # Detect languages first
        languages = self.ingestor._detect_languages(Path(repo_path))

        # Collect files (accessing a protected method for testing)
        files = self.ingestor._collect_files(Path(repo_path), languages)

        # Verify collected files
        file_paths = list(files.keys())

        # The exact list of files collected may vary based on the implementation
        # Let's just verify we found some basic Python files
        self.assertTrue(any(p.endswith(".py") for p in file_paths))

        # And verify we found some files in each language's directory
        csharp_files = [p for p in file_paths if "csharp" in p.lower()]
        react_files = [p for p in file_paths if "react" in p.lower()]

        self.assertTrue(len(csharp_files) > 0, "No C# files found")
        self.assertTrue(len(react_files) > 0, "No React files found")

        # Clean up
        cleanup_sample_repo(repo_path)

    def test_analyze_dependencies(self):
        # Create a sample repository
        repo_path = create_sample_repo()

        # Detect languages first
        languages = self.ingestor._detect_languages(Path(repo_path))

        # Collect files
        files = self.ingestor._collect_files(Path(repo_path), languages)

        # Analyze dependencies (accessing a protected method for testing)
        dependencies = self.ingestor._analyze_dependencies(files, languages)

        # Verify dependencies structure
        self.assertIsInstance(dependencies, dict)

        # Clean up
        cleanup_sample_repo(repo_path)

    def test_build_tree_structure(self):
        # Create a sample file dictionary
        files = {
            "main.py": "content1",
            "utils.py": "content2",
            os.path.join("folder", "file.py"): "content3",
            os.path.join("folder", "subfolder", "file.js"): "content4"
        }

        # Build tree structure (accessing a protected method for testing)
        tree = self.ingestor._build_tree_structure(files)

        # Verify tree structure
        self.assertIn("main.py", tree)
        self.assertIn("utils.py", tree)
        self.assertIn("folder", tree)
        self.assertIn("file.py", tree["folder"])
        self.assertIn("subfolder", tree["folder"])
        self.assertIn("file.js", tree["folder"]["subfolder"])

    def test_full_ingest(self):
        # Create a sample repository
        repo_path = create_sample_repo()

        # Ingest the repository
        repo_info = self.ingestor.ingest(repo_path)

        # Verify the result is a RepositoryInfo object
        self.assertIsInstance(repo_info, RepositoryInfo)

        # Verify basic structure
        self.assertEqual(repo_info.root_path, Path(repo_path))
        self.assertTrue("python" in repo_info.languages)
        self.assertTrue(len(repo_info.files) > 0)
        self.assertIsInstance(repo_info.file_dependencies, dict)
        self.assertIsInstance(repo_info.metadata, dict)
        self.assertIsInstance(repo_info.tree_structure, dict)
        self.assertIsInstance(repo_info.token_info, dict)
        self.assertIsInstance(repo_info.function_info, dict)

        # Clean up
        cleanup_sample_repo(repo_path)

    def test_token_estimate_only(self):
        # Create a sample repository
        repo_path = create_sample_repo()

        # Ingest the repository with token_estimate_only=True
        repo_info = self.ingestor.ingest(repo_path, token_estimate_only=True)

        # Verify the result is a RepositoryInfo object
        self.assertIsInstance(repo_info, RepositoryInfo)

        # Verify basic structure
        self.assertEqual(repo_info.root_path, Path(repo_path))
        self.assertTrue("python" in repo_info.languages)
        self.assertTrue(len(repo_info.files) > 0)

        # These should be empty or minimal with token_estimate_only=True
        self.assertEqual(repo_info.file_dependencies, {})
        self.assertEqual(len(repo_info.function_info), 0)

        # Token info should still be populated
        self.assertIsInstance(repo_info.token_info, dict)
        self.assertIn("total_tokens", repo_info.token_info)

        # Clean up
        cleanup_sample_repo(repo_path)

    def test_language_filtering(self):
        """
        Test filtering by specific languages
        """
        repo_path = create_sample_repo()

        try:
            # First analyze with all languages to confirm what's available
            all_langs_repo_info = self.ingestor.ingest(repo_path)

            # Verify all languages are detected
            self.assertIn("python", all_langs_repo_info.languages)
            self.assertIn("csharp", all_langs_repo_info.languages)
            self.assertIn("react", all_langs_repo_info.languages)
            self.assertIn("yaml", all_langs_repo_info.languages)

            # Get the full list of files to verify against later
            all_files = set(all_langs_repo_info.files.keys())

            # Get all YAML files to check against later
            all_yaml_files = {f for f in all_files if f.endswith('.yml') or f.endswith('.yaml')}

            # Test 1: Python-only filter
            python_repo_info = self.ingestor.ingest(repo_path, languages_filter=["python"])

            # Verify language detection works
            self.assertEqual(python_repo_info.languages, ["python"])

            # Get Python-only files
            python_files = set(python_repo_info.files.keys())

            # Debug output for understanding what files were included
            print("\nAll files:", all_files)
            print("Python filtered files:", python_files)

            # Ensure no YAML files were included
            python_yaml_files = {f for f in python_files if f.endswith('.yml') or f.endswith('.yaml')}
            self.assertEqual(python_yaml_files, set(),
                             f"YAML files found in Python-only analysis: {python_yaml_files}")

            # Test 2: Filter Python + YAML
            py_yaml_repo_info = self.ingestor.ingest(repo_path, languages_filter=["python", "yaml"])

            # Verify language detection
            self.assertSetEqual(set(py_yaml_repo_info.languages), {"python", "yaml"})

            # Get Python+YAML files
            py_yaml_files = set(py_yaml_repo_info.files.keys())

            # Ensure YAML files are now included
            self.assertTrue(all_yaml_files.issubset(py_yaml_files),
                            f"Not all YAML files included. Expected {all_yaml_files}, got intersection: {all_yaml_files.intersection(py_yaml_files)}")

            # Test 3: Case insensitivity
            upper_repo_info = self.ingestor.ingest(repo_path, languages_filter=["PYTHON", "YAML"])

            # Verify languages are detected correctly despite case differences
            self.assertSetEqual(set(upper_repo_info.languages), {"python", "yaml"})

        finally:
            # Clean up
            cleanup_sample_repo(repo_path)

if __name__ == "__main__":
    unittest.main()