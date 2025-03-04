import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.tree import Tree
from rich.text import Text

from .core import RepositoryIngestor
from .formatters import FORMATTERS

console = Console()

TOOL_DESCRIPTION = """
Repo Ingestor is a professional tool that converts code repositories into a single file containing all code, dependencies, 
file names, and their interconnections. Designed to help developers understand, document, and prepare repositories 
for use with Large Language Models (LLMs).
"""

EXAMPLE_USAGE = """
Examples:
  # Analyze the current directory
  repo-ingestor

  # Analyze a specific repository
  repo-ingestor /path/to/repository

  # Change output format to JSON
  repo-ingestor --format json

  # Exclude test files and directories
  repo-ingestor --no-tests

  # Combine multiple options
  repo-ingestor --format markdown --max-file-size 2048 --keep-comments --no-tests

  # Show help information
  repo-ingestor --help
"""


def format_file_size(size_in_bytes):
    """Format file size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"


def print_intro(repo_path):
    """Print an introduction panel for the analysis."""
    console.print(Panel.fit(
        f"[bold cyan]Repo Ingestor[/bold cyan] - Analyzing Repository: [bold yellow]{repo_path}[/bold yellow]",
        border_style="cyan",
        padding=(1, 2)
    ))


def print_summary(repo_info, output_path, format_name, removed_comments):
    """Print a summary of the repository analysis."""
    token_table = Table(title="Token Information")
    token_table.add_column("Category", style="cyan")
    token_table.add_column("Count", style="yellow")

    token_info = repo_info.token_info
    token_table.add_row("Total Estimated Tokens", f"{token_info.get('total_tokens', 0):,}")
    token_table.add_row("Structure Tokens", f"{token_info.get('structure_tokens', 0):,}")

    top_files_table = Table(title="Top Files by Token Count")
    top_files_table.add_column("File", style="cyan")
    top_files_table.add_column("Tokens", justify="right", style="yellow")

    top_files = token_info.get('top_files_by_tokens', [])
    for file_path, count in top_files[:5]:  # Show top 5 files
        top_files_table.add_row(file_path, f"{count:,}")

    function_table = Table(title="Function Analysis")
    function_table.add_column("Category", style="cyan")
    function_table.add_column("Count", style="yellow")

    function_info = repo_info.function_info
    function_table.add_row("Total Functions", str(function_info.get('total_function_count', 0)))

    called_functions_table = Table(title="Most Called Functions")
    called_functions_table.add_column("Function", style="cyan")
    called_functions_table.add_column("Called By", justify="right", style="yellow")

    highly_connected = function_info.get('highly_connected', [])
    for func, count in highly_connected[:5]:  # Show top 5 called functions
        called_functions_table.add_row(func, f"{count} other functions")

    output_panel = Panel.fit(
        f"[bold green]✅ Analysis Complete![/bold green]\n"
        f"Output written to: [bold cyan]{output_path}[/bold cyan]\n"
        f"Format: [yellow]{format_name}[/yellow]"
        + ("\n[dim]Comments were removed from files[/dim]" if removed_comments else ""),
        title="Summary",
        border_style="green",
        padding=(1, 2)
    )

    console.print()
    console.print(output_panel)
    console.print()

    console.print(token_table)
    console.print()
    console.print(top_files_table)
    console.print()
    console.print(function_table)
    console.print()
    if highly_connected:
        console.print(called_functions_table)


def format_help_custom(ctx, formatter):
    """Custom formatter for the help command."""
    formatter.write(TOOL_DESCRIPTION)
    formatter.write("\n\n")

    with formatter.section("Usage"):
        formatter.write_text("repo-ingestor [OPTIONS] [REPO_PATH]")

    formatter.write("\n")
    with formatter.section("Main Options"):
        for param in ctx.command.get_params(ctx):
            if param.name in ["output", "format"]:
                help_record = param.get_help_record(ctx)
                if help_record:
                    formatter.write_dl([help_record])

    formatter.write("\n")
    with formatter.section("File Selection Options"):
        for param in ctx.command.get_params(ctx):
            if param.name in ["max_file_size", "exclude", "keep_comments", "depth", "no_tests"]:
                help_record = param.get_help_record(ctx)
                if help_record:
                    formatter.write_dl([help_record])

    formatter.write("\n")
    with formatter.section("Performance Options"):
        for param in ctx.command.get_params(ctx):
            if param.name in ["minimal", "token_estimate_only"]:
                help_record = param.get_help_record(ctx)
                if help_record:
                    formatter.write_dl([help_record])

    formatter.write("\n")
    with formatter.section("Other Options"):
        formatter.write_dl([
            (("-h, --help"), ("Show this help message and exit."))
        ])

    formatter.write("\n")
    formatter.write(EXAMPLE_USAGE)


@click.command(context_settings=dict(
    help_option_names=['-h', '--help'],
    max_content_width=250
))
@click.argument("repo_path", type=click.Path(exists=True), required=False,
                metavar="[REPO_PATH]")
@click.option(
    "-o", "--output",
    type=click.Path(writable=True),
    help="Output file path where analysis results will be written."
)
@click.option(
    "-f", "--format",
    type=click.Choice(list(FORMATTERS.keys())),
    default="markdown",
    help="Output format for the analysis report. Options: markdown (default), json (summary only), text"
)
@click.option(
    "--max-file-size",
    type=int,
    default=1024,
    help="Maximum file size in KB to include in analysis. Larger files will be skipped. Default: 1024KB"
)
@click.option(
    "--exclude",
    multiple=True,
    help="Additional file patterns to exclude from analysis. Can be used multiple times. Example: --exclude \"*.log\" --exclude \"temp/*\""
)
@click.option(
    "--keep-comments",
    default=False,
    help="Whether to preserve comments in output code. Default: False"
)
@click.option(
    "--minimal",
    default=False,
    help="Use minimal output mode with less verbose console output. Useful for automated environments. Default: False"
)
@click.option(
    "--depth",
    type=int,
    default=None,
    help="Maximum directory depth to analyze. Use to limit analysis to top-level directories. Default: unlimited"
)
@click.option(
    "--token-estimate-only",
    is_flag=True,
    default=False,
    help="Perform fast token count estimation only, skipping full dependency and function analysis"
)
@click.option(
    "--no-tests",
    is_flag=True,
    default=False,
    help="Exclude test files and directories from analysis. This will exclude common test patterns across languages."
)
def main(repo_path, output, format, max_file_size, exclude, keep_comments, minimal, depth, token_estimate_only, no_tests):
    """
    Analyze a code repository and produce a comprehensive single-file output.

    If REPO_PATH is not specified, the current directory will be used.
    """
    ctx = click.get_current_context()
    ctx.command.format_help = lambda ctx, formatter: format_help_custom(ctx, formatter)

    try:
        if repo_path is None:
            repo_path = os.getcwd()
        repo_path = Path(repo_path).resolve()

        if not minimal:
            print_intro(repo_path)

        from .config import Config
        config = Config()
        config.max_file_size_kb = max_file_size
        config.max_depth = depth
        config.remove_comments = not keep_comments

        if exclude:
            for pattern in exclude:
                config.common_exclude_patterns.add(pattern)

        # Add test exclusion patterns if --no-tests flag is set
        if no_tests:
            # Python test patterns
            config.common_exclude_patterns.add("tests/")
            config.common_exclude_patterns.add("test_*.py")
            config.common_exclude_patterns.add("*_test.py")

            # C# test patterns
            config.common_exclude_patterns.add("**/Tests/")
            config.common_exclude_patterns.add("*Tests.cs")
            config.common_exclude_patterns.add("*Test.cs")
            config.common_exclude_patterns.add("*Specs.cs")

            # JavaScript/React test patterns
            config.common_exclude_patterns.add("**/__tests__/")
            config.common_exclude_patterns.add("*.test.js")
            config.common_exclude_patterns.add("*.test.jsx")
            config.common_exclude_patterns.add("*.test.ts")
            config.common_exclude_patterns.add("*.test.tsx")
            config.common_exclude_patterns.add("*.spec.js")
            config.common_exclude_patterns.add("*.spec.jsx")
            config.common_exclude_patterns.add("*.spec.ts")
            config.common_exclude_patterns.add("*.spec.tsx")

        with Progress(
                SpinnerColumn(),
                TextColumn("[bold cyan]{task.description}[/bold cyan]"),
                BarColumn(),
                TaskProgressColumn(),
                expand=True,
                console=console
        ) as progress:
            ingestor = RepositoryIngestor(config, progress if not minimal else None)

            task = progress.add_task("Analyzing repository...", total=100)
            repo_info = ingestor.ingest(repo_path, token_estimate_only=token_estimate_only)
            progress.update(task, completed=100)

        if output is None:
            if format == "text":
                output = f"repo_structure.txt"
            elif format == "markdown":
                output = f"repo_structure.md"
            else:
                output = f"repo_structure.{format}"

        formatter_class = FORMATTERS[format]
        formatter = formatter_class()

        if not minimal:
            console.print(f"Writing output to: [cyan]{output}[/cyan]")

        with open(output, "w", encoding="utf-8") as f:
            formatter.format(repo_info, f)

        if not minimal:
            if token_estimate_only:
                token_table = Table(title="Token Information")
                token_table.add_column("Category", style="cyan")
                token_table.add_column("Count", style="yellow")

                token_info = repo_info.token_info
                token_table.add_row("Total Estimated Tokens", f"{token_info.get('total_tokens', 0):,}")
                token_table.add_row("Structure Tokens", f"{token_info.get('structure_tokens', 0):,}")

                top_files_table = Table(title="Top Files by Token Count")
                top_files_table.add_column("File", style="cyan")
                top_files_table.add_column("Tokens", justify="right", style="yellow")

                top_files = token_info.get('top_files_by_tokens', [])
                for file_path, count in top_files[:5]:  # Show top 5 files
                    top_files_table.add_row(file_path, f"{count:,}")

                console.print(Panel.fit(
                    f"[bold green]✅ Token Estimation Complete![/bold green]\n"
                    f"Output written to: [bold cyan]{output}[/bold cyan]",
                    title="Token Summary",
                    border_style="green",
                    padding=(1, 2)
                ))
                console.print()
                console.print(token_table)
                console.print()
                console.print(top_files_table)
            else:
                print_summary(repo_info, output, format, not keep_comments)
        else:
            console.print(f"Analysis complete. Output written to: {output}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        if not minimal:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()