# Repo Ingestor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A professional tool that converts code repositories into a single file containing all code, dependencies, file names, and their interconnections. Designed to help developers document and analyze codebases, understand dependencies, and prepare repositories for use with Large Language Models (LLMs).

## 🚀 Features

- **Multi-language Support** - Analyze Python, C#, and React projects
- **Comprehensive Analysis** - Extract dependencies, file structures, and metadata
- **Function Call Graph** - Visualize function relationships and identify key entry points
- **LLM Token Estimation** - Calculate token counts for different AI model context windows
- **Multiple Output Formats** - Export as Markdown, JSON, or plain text
- **Performance Optimized** - Smart file filtering and size limiting
- **Customizable** - Extensive pattern matching for file inclusion/exclusion

## 📋 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/repo-ingestor.git
cd repo-ingestor

# Install the package
pip install -e .

# Or install directly from PyPI
pip install repo-ingestor
```

## 🔍 Usage

### Basic Usage

```bash
# Analyze the current directory
repo-ingestor

# Analyze a specific repository
repo-ingestor /path/to/repository
```

### Output Options

```bash
# Change output format (markdown, json (summary only), text)
repo-ingestor --format text

# Specify custom output file
repo-ingestor --output repo-analysis.md
```

### Analysis Options

```bash
# Set maximum file size to include (in KB)
repo-ingestor --max-file-size 2048

# Limit directory depth for large repositories
repo-ingestor --depth 3

# Fast token estimation only (skips dependency and function analysis)
repo-ingestor --token-estimate-only
```

### File Selection

```bash
# Keep comments in the output
repo-ingestor --keep-comments

# Exclude test files and directories
repo-ingestor --no-tests

# Exclude specific file patterns
repo-ingestor --exclude "*.log" --exclude "temp/*"
```

### Other Options

```bash
# Use minimal output mode (less verbose)
repo-ingestor --minimal

# Get full help
repo-ingestor --help
```

## 📊 Output Examples

### Token Information

```
Token Count Information:
- Total Estimated Tokens: 14,943
- Structure Tokens: 472

Top Files by Token Count:
| File                             | Tokens |
| -------------------------------- | ------ |
| repo_ingestor\formatters.py      | 2,413  |
| repo_ingestor\cli.py             | 2,245  |
| repo_ingestor\core.py            | 1,607  |
```

### Function Call Graph

```
Function Call Graph:
- Total Functions: 55

Most Called Functions:
| Function                  | Called By      |
| ------------------------- | -------------- |
| get_file_content          | 2 other functions |
| build_call_graph_from_files | 1 other functions |
```

### Directory Structure

```
- 📄 README.md
- 📁 **repo_ingestor/**
  - 📄 __init__.py
  - 📄 __main__.py
  - 📄 cli.py
  - 📄 config.py
  ...
```

## 🔧 Supported Languages

### Python
- Analyzes `.py` files, requirements, and configuration files
- Detects imports, packages, and entry points
- Builds detailed function call graphs

### C#
- Analyzes `.cs`, `.csproj`, `.sln` files, and NuGet packages
- Detects namespace imports and project references
- Extracts target framework information

### React
- Analyzes `.jsx`, `.tsx`, `.js`, `.ts` files and package dependencies
- Parses package.json for dependencies and scripts
- Identifies component imports and exports

## 🏗️ Architecture

Repo Ingestor is designed with a modular architecture:

- **Core Module**: Central orchestration of the analysis process
- **Language Handlers**: Specialized modules for each supported language
- **Formatters**: Output generation in various formats
- **Analyzers**: Function call graph and token estimation
- **Utilities**: File handling, pattern matching, and comment removal

## 📝 Configuration

The tool provides extensive configuration options:

- Common include/exclude patterns for repository scanning
- Language-specific file patterns
- File size limits and directory depth limits
- Comment removal options
- Performance optimization settings

## 🧰 Requirements

- Python 3.7 or higher
- click>=8.0.0
- rich>=10.0.0
- tqdm>=4.62.0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.