"""
Configuration settings for the repository ingestor.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class LanguageConfig:
    """Configuration for a specific language."""
    name: str
    extensions: Set[str] = field(default_factory=set)
    include_patterns: Set[str] = field(default_factory=set)
    exclude_patterns: Set[str] = field(default_factory=set)
    config_files: Set[str] = field(default_factory=set)


@dataclass
class Config:
    common_include_patterns: Set[str] = field(default_factory=lambda: {
        "Dockerfile",
        "docker-compose.yml",
        ".gitignore",
        "README.md",
        "LICENSE",
        ".env.example",
        "Makefile",
        "requirements.txt",
        "package.json",
        "setup.py",
        "*.config"
    })

    common_exclude_patterns: Set[str] = field(default_factory=lambda: {
        # Git
        ".git/",
        # Python
        "__pycache__/",
        "*.pyc",
        "*.pyd",
        "*.pyo",
        # Binary and compiled files
        "*.dll",
        "*.exe",
        "*.obj",
        "*.o",
        "*.a",
        "*.lib",
        "*.so",
        "*.dylib",
        # Visual Studio/C# files
        "*.ncb",
        "*.sdf",
        "*.suo",
        "*.pdb",
        "*.ipdb",
        "*.pgc",
        "*.pgd",
        "*.rsp",
        "*.sbr",
        "*.tlb",
        "*.tli",
        "*.tlh",
        "*.tmp",
        "*.tmp_proj",
        "*.log",
        "*.vspscc",
        "*.vssscc",
        ".builds",
        "*.pidb",
        "*.svclog",
        "*.scc",
        "*.psess",
        "*.vsp",
        "*.vspx",
        # Build output folders
        "**/bin/",
        "**/obj/",
        "**/build/",
        "**/dist/",
        # NPM
        "**/node_modules/",
        # Virtual environments
        "**/.venv/",
        "**/venv/",
        "**/env/",
        "**/.env/",
        "**/ENV/",
        # Other
        "**/.DS_Store",
        "**/Lib/site-packages/"
    })

    languages: Dict[str, LanguageConfig] = field(default_factory=dict)

    max_file_size_kb: int = 1024  # Skip files larger than this size
    max_depth: int = None
    remove_comments: bool = True

    def __post_init__(self):
        # Normalize all patterns to use forward slashes
        self.common_include_patterns = {p.replace('\\', '/') for p in self.common_include_patterns}
        self.common_exclude_patterns = {p.replace('\\', '/') for p in self.common_exclude_patterns}

        # Ensure directory patterns end with a slash for proper matching
        normalized_exclude = set()
        for pattern in self.common_exclude_patterns:
            if pattern.endswith('/'):
                normalized_exclude.add(pattern)
            elif pattern.endswith('/**'):
                normalized_exclude.add(pattern[:-3] + '/')
            elif '**/' in pattern and not pattern.endswith('*'):
                # For patterns like **/obj, ensure they become **/obj/
                if not any(c in pattern.split('**/')[1] for c in '.*?[]'):
                    normalized_exclude.add(pattern + '/')
                else:
                    normalized_exclude.add(pattern)
            else:
                normalized_exclude.add(pattern)

        self.common_exclude_patterns = normalized_exclude

        self.languages["python"] = LanguageConfig(
            name="Python",
            extensions={".py"},
            include_patterns={"pyproject.toml", "setup.cfg", "pytest.ini", "tox.ini", "requirements*.txt"},
            exclude_patterns=set(),
            config_files={"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"}
        )

        self.languages["csharp"] = LanguageConfig(
            name="C#",
            extensions={".cs", ".csproj", ".sln"},
            include_patterns={"*.config", "App.config", "Web.config", "packages.config", "*.props", "*.targets"},
            exclude_patterns=set(),
            config_files={"*.csproj", "*.sln", "packages.config", "NuGet.config"}
        )

        self.languages["react"] = LanguageConfig(
            name="React",
            extensions={".jsx", ".tsx", ".js", ".ts"},
            include_patterns={"package.json", "tsconfig.json", ".babelrc", ".eslintrc*", "webpack.config.js", "next.config.js", "vite.config.js"},
            exclude_patterns={"*.d.ts"},
            config_files={"package.json", "tsconfig.json", ".babelrc", "webpack.config.js"}
        )


# Default configuration
DEFAULT_CONFIG = Config()