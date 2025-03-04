import unittest

from repo_ingestor.config import Config, LanguageConfig, DEFAULT_CONFIG


class TestLanguageConfig(unittest.TestCase):

    def test_language_config_creation(self):
        # Create a language config
        config = LanguageConfig(
            name="TestLang",
            extensions={".tl", ".test"},
            include_patterns={"*.test", "test.config"},
            exclude_patterns={"*.tmp"},
            config_files={"test.config"}
        )

        # Verify attributes
        self.assertEqual(config.name, "TestLang")
        self.assertEqual(config.extensions, {".tl", ".test"})
        self.assertEqual(config.include_patterns, {"*.test", "test.config"})
        self.assertEqual(config.exclude_patterns, {"*.tmp"})
        self.assertEqual(config.config_files, {"test.config"})

    def test_language_config_default_values(self):
        # Create a language config with minimal arguments
        config = LanguageConfig(name="MinimalLang")

        # Verify default values
        self.assertEqual(config.extensions, set())
        self.assertEqual(config.include_patterns, set())
        self.assertEqual(config.exclude_patterns, set())
        self.assertEqual(config.config_files, set())


class TestConfig(unittest.TestCase):

    def test_config_creation(self):
        # Create a config object
        config = Config()

        # Verify default values
        self.assertTrue(len(config.common_include_patterns) > 0)
        self.assertTrue(len(config.common_exclude_patterns) > 0)
        self.assertGreater(len(config.languages), 0)
        self.assertEqual(config.max_file_size_kb, 1024)
        self.assertIsNone(config.max_depth)
        self.assertTrue(config.remove_comments)

    def test_config_languages(self):
        # Create a config object
        config = Config()

        # Verify languages
        self.assertIn("python", config.languages)
        self.assertIn("csharp", config.languages)
        self.assertIn("react", config.languages)

        # Check language configs
        python_config = config.languages["python"]
        self.assertEqual(python_config.name, "Python")
        self.assertIn(".py", python_config.extensions)

        csharp_config = config.languages["csharp"]
        self.assertEqual(csharp_config.name, "C#")
        self.assertIn(".cs", csharp_config.extensions)

        react_config = config.languages["react"]
        self.assertEqual(react_config.name, "React")
        self.assertIn(".jsx", react_config.extensions)

    def test_config_post_init(self):
        # Create a config with Windows-style backslashes
        config = Config()
        config.common_include_patterns = {"path\\to\\file", "another\\path"}
        config.common_exclude_patterns = {"exclude\\path", "another\\exclude"}

        # Call __post_init__ manually (normally called during initialization)
        config.__post_init__()

        # Verify paths are normalized to forward slashes
        for pattern in config.common_include_patterns:
            self.assertNotIn("\\", pattern)

        for pattern in config.common_exclude_patterns:
            self.assertNotIn("\\", pattern)

    def test_default_config(self):
        # Verify the default config is a Config object
        self.assertIsInstance(DEFAULT_CONFIG, Config)

        # Verify it has the expected languages
        self.assertIn("python", DEFAULT_CONFIG.languages)
        self.assertIn("csharp", DEFAULT_CONFIG.languages)
        self.assertIn("react", DEFAULT_CONFIG.languages)


if __name__ == "__main__":
    unittest.main()