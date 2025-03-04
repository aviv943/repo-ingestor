"""
Utilities for estimating token counts for LLM processing.
"""
import re
from typing import Dict, Any, List, Tuple


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text.

    This is a heuristic estimation based on common tokenization patterns.
    It's not exact but should give a reasonable approximation.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Count words (splitting on whitespace)
    words = re.findall(r'\S+', text)
    word_count = len(words)

    # Count punctuation and symbols that are typically separate tokens
    punctuation_count = len(re.findall(r'[.,;:!?()[\]{}"`]', text))

    # Count common programming tokens
    code_tokens = len(re.findall(r'[=+\-*/><&|^~%]', text))

    # Count line breaks which are often separate tokens
    newline_count = text.count('\n')

    # Special sequences that are often a single token but would be counted as multiple words
    # Common programming words that are likely single tokens
    common_sequences = [
        'if', 'else', 'for', 'while', 'function', 'return', 'import',
        'class', 'def', 'from', 'try', 'except', 'finally', 'with',
        'async', 'await', 'as', 'in', 'is', 'not', 'and', 'or'
    ]

    special_sequence_count = sum(text.count(f' {seq} ') for seq in common_sequences)

    # A decent approximation: words + punctuation + symbols + newlines - special sequences
    # with a small multiplier to account for subword tokenization
    token_estimate = int((word_count + punctuation_count + code_tokens + newline_count - special_sequence_count) * 1.1)

    return max(1, token_estimate)  # Ensure at least 1 token


def estimate_repository_tokens(repo_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate token counts for a repository.

    Args:
        repo_info: Repository information with file contents

    Returns:
        Dictionary with token count information
    """
    total_tokens = 0
    file_tokens = {}

    # Estimate tokens for each file
    for file_path, content in repo_info.get('files', {}).items():
        tokens = estimate_tokens(content)
        file_tokens[file_path] = tokens
        total_tokens += tokens

    # Estimate tokens for metadata and other structures
    # This is a rough estimate for structure overhead
    metadata_str = str(repo_info.get('metadata', {}))
    tree_str = str(repo_info.get('tree_structure', {}))
    deps_str = str(repo_info.get('file_dependencies', {}))

    metadata_tokens = estimate_tokens(metadata_str)
    tree_tokens = estimate_tokens(tree_str)
    deps_tokens = estimate_tokens(deps_str)

    structure_tokens = metadata_tokens + tree_tokens + deps_tokens
    total_tokens += structure_tokens

    # Sort files by token count to show the largest files
    sorted_files = sorted(file_tokens.items(), key=lambda x: x[1], reverse=True)
    top_files = sorted_files[:10]  # Top 10 files by token count

    # Calculate size tiers for LLM context windows
    context_tiers = [
        ('4K tokens (GPT-3.5)', 4000),
        ('8K tokens (Basic)', 8000),
        ('16K tokens (GPT-3.5 Turbo)', 16000),
        ('32K tokens (GPT-4 Turbo)', 32000),
        ('128K tokens (Claude Opus)', 128000),
    ]

    fits_in = [name for name, limit in context_tiers if total_tokens <= limit]
    exceeds = [name for name, limit in context_tiers if total_tokens > limit]

    return {
        'total_tokens': total_tokens,
        'structure_tokens': structure_tokens,
        'file_tokens': file_tokens,
        'top_files_by_tokens': top_files,
        'fits_in_models': fits_in,
        'exceeds_models': exceeds
    }