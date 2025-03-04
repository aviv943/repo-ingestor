import os
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass
class LanguageConfig:
    """Configuration for a specific programming language or file format."""
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

        # Compiled binaries
        "*.dll",
        "*.exe",
        "*.obj",
        "*.o",
        "*.a",
        "*.lib",
        "*.so",
        "*.dylib",

        # Visual Studio and other IDEs
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

        # Build directories
        "**/bin/",
        "**/obj/",
        "**/build/",
        "**/dist/",

        # Node.js
        "**/node_modules/",

        # Python virtual environments
        "**/.venv/",
        "**/venv/",
        "**/env/",
        "**/.env/",
        "**/ENV/",

        # Misc
        "**/.DS_Store",
        "**/Lib/site-packages/"
    })

    languages: Dict[str, LanguageConfig] = field(default_factory=dict)

    max_file_size_kb: int = 1024  # Skip files larger than this size
    max_depth: int = None
    remove_comments: bool = True

    def __post_init__(self):
        # Normalize path separators in patterns
        self.common_include_patterns = {p.replace('\\', '/') for p in self.common_include_patterns}
        self.common_exclude_patterns = {p.replace('\\', '/') for p in self.common_exclude_patterns}

        normalized_exclude = set()
        for pattern in self.common_exclude_patterns:
            if pattern.endswith('/'):
                normalized_exclude.add(pattern)
            elif pattern.endswith('/**'):
                normalized_exclude.add(pattern[:-3] + '/')
            elif '**/' in pattern and not pattern.endswith('*'):
                # If pattern has a globstar but doesn't end with a wildcard,
                # add a trailing slash to also match directories
                if not any(c in pattern.split('**/')[1] for c in '.*?[]'):
                    normalized_exclude.add(pattern + '/')
                else:
                    normalized_exclude.add(pattern)
            else:
                normalized_exclude.add(pattern)

        self.common_exclude_patterns = normalized_exclude

        # Configure Python language
        self.languages["python"] = LanguageConfig(
            name="Python",
            extensions={".py"},
            include_patterns={"pyproject.toml", "setup.cfg", "pytest.ini", "tox.ini", "requirements*.txt"},
            exclude_patterns=set(),
            config_files={"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"}
        )

        # Configure C# language
        self.languages["csharp"] = LanguageConfig(
            name="C#",
            extensions={".cs", ".csproj", ".sln"},
            include_patterns={"*.config", "App.config", "Web.config", "packages.config", "*.props", "*.targets"},
            exclude_patterns=set(),
            config_files={"*.csproj", "*.sln", "packages.config", "NuGet.config"}
        )

        # Configure React language
        self.languages["react"] = LanguageConfig(
            name="React",
            extensions={".jsx", ".tsx", ".js", ".ts"},
            include_patterns={"package.json", "tsconfig.json", ".babelrc", ".eslintrc*", "webpack.config.js", "next.config.js", "vite.config.js"},
            exclude_patterns={"*.d.ts"},
            config_files={"package.json", "tsconfig.json", ".babelrc", "webpack.config.js"}
        )

        # Configure YAML language
        self.languages["yaml"] = LanguageConfig(
            name="YAML",
            extensions={".yml", ".yaml"},
            include_patterns={
                "docker-compose*.yml", "docker-compose*.yaml",
                ".github/workflows/*.yml", ".github/workflows/*.yaml",
                "kubernetes/*.yml", "kubernetes/*.yaml",
                "k8s/*.yml", "k8s/*.yaml",
                "helm/**/*.yml", "helm/**/*.yaml",
                ".gitlab-ci.yml", "cloudbuild.yaml",
                "appveyor.yml", "circle.yml", "travis.yml", ".travis.yml",
                "**/Chart.yaml", "**/values.yaml",
                "ansible/*.yml", "ansible/*.yaml",
                "*.yaml", "*.yml"  # Include all YAML files as a fallback
            },
            exclude_patterns=set(),
            config_files={"docker-compose.yml", "docker-compose.yaml", ".github/workflows/*.yml"}
        )

    def add_exclude_pattern(self, pattern: str) -> None:
        """
        Add an exclude pattern, ensuring it's properly formatted for matching.

        Args:
            pattern: The pattern to add
        """
        # Normalize separator to forward slash
        pattern = pattern.replace('\\', '/')

        # Ensure directory patterns end with a slash
        if os.path.isdir(pattern) and not pattern.endswith('/'):
            pattern += '/'

        # Add both with and without leading dot for flexibility
        self.common_exclude_patterns.add(pattern)

        # If pattern starts with dot, add version without dot
        if pattern.startswith('.'):
            self.common_exclude_patterns.add(pattern[1:])

        # If pattern doesn't end with slash or wildcard, add wildcard version
        if not pattern.endswith('/') and not pattern.endswith('*'):
            if os.path.isdir(pattern):
                self.common_exclude_patterns.add(pattern + '**/*')
            else:
                self.common_exclude_patterns.add(pattern + '*')

DEFAULT_CONFIG = Config()