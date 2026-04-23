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
    template: str = typer.Option(
        "basic", "--template", "-t",
        help="Project template: basic, api, or database",
    ),
):
    """Scaffold a new MCP server project with FastMCP."""
    from .init_cmd import run_init

    run_init(name, template=template)


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


@app.command()
def proxy(
    server: str = typer.Argument(
        ..., help="Server to proxy (Python file or command)",
    ),
):
    """Log all JSON-RPC traffic between an MCP client and server."""
    from .proxy_cmd import run_proxy

    run_proxy(server)


@app.command()
def diff(
    server_a: str = typer.Argument(..., help="First server (baseline)"),
    server_b: str = typer.Argument(..., help="Second server (new version)"),
):
    """Compare capabilities of two MCP servers side by side."""
    from .diff_cmd import run_diff

    run_diff(server_a, server_b)


@app.command()
def bench(
    server: str = typer.Argument(
        ..., help="Server to benchmark (Python file or command)",
    ),
    tool: Optional[str] = typer.Option(
        None, "--tool", "-t", help="Benchmark a specific tool (default: all)",
    ),
    params: Optional[str] = typer.Option(
        None, "--params", "-p", help="JSON parameters for the tool",
    ),
    runs: int = typer.Option(
        10, "--runs", "-n", help="Number of benchmark runs per tool",
    ),
):
    """Benchmark tool response times on an MCP server."""
    from .bench_cmd import run_bench

    run_bench(server, tool=tool, params=params, runs=runs)


if __name__ == "__main__":
    app()
