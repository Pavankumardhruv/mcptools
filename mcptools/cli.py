"""mcptools — The Swiss Army knife for MCP server development."""

from typing import Optional

import typer
from rich.console import Console

from . import __version__

app = typer.Typer(
    name="mcptools",
    help="The Swiss Army knife for MCP server development.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"mcptools [cyan]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit.",
    ),
):
    pass


@app.command()
def init(
    name: str = typer.Argument(..., help="Name for the new MCP server project"),
):
    """Scaffold a new MCP server project with FastMCP."""
    from .init_cmd import run_init

    run_init(name)


@app.command()
def inspect(
    server: str = typer.Argument(
        ..., help="Server to inspect (Python file or command)",
    ),
    json: bool = typer.Option(
        False, "--json", "-j", help="Output raw JSON instead of tables",
    ),
):
    """Connect to an MCP server and list its tools, resources, and prompts."""
    from .inspect_cmd import run_inspect

    run_inspect(server, json_output=json)


@app.command()
def test(
    server: str = typer.Argument(
        ..., help="Server to test (Python file or command)",
    ),
    tool: Optional[str] = typer.Option(
        None, "--tool", "-t", help="Tool name for non-interactive mode",
    ),
    params: Optional[str] = typer.Option(
        None, "--params", "-p", help='JSON parameters, e.g. \'{"name": "World"}\'',
    ),
):
    """Interactively test tools on an MCP server."""
    from .test_cmd import run_test

    run_test(server, tool_name=tool, params=params)


@app.command()
def validate(
    server: str = typer.Argument(
        ..., help="Server to validate (Python file or command)",
    ),
    min_score: int = typer.Option(
        0, "--min-score", "-m", help="Exit with error if score is below this threshold",
    ),
):
    """Validate an MCP server against best practices."""
    from .validate_cmd import run_validate

    score = run_validate(server)
    if min_score > 0 and score < min_score:
        console.print(
            f"[red]Score {score} is below minimum {min_score}[/]"
        )
        raise typer.Exit(1)


@app.command()
def dev(
    server: str = typer.Argument(
        ..., help="Server to run in dev mode (Python file or command)",
    ),
):
    """Run an MCP server with auto-reload on file changes."""
    from .dev_cmd import run_dev

    run_dev(server)


@app.command()
def docs(
    server: str = typer.Argument(
        ..., help="Server to document (Python file or command)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Write to file instead of stdout",
    ),
):
    """Auto-generate Markdown documentation from an MCP server."""
    from .docs_cmd import run_docs

    run_docs(server, output=output)


if __name__ == "__main__":
    app()
