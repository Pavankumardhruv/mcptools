"""Scaffold a new MCP server project."""

import os
from pathlib import Path

from rich.console import Console

console = Console()

SERVER_TEMPLATE = '''\
from fastmcp import FastMCP

mcp = FastMCP("{name}")


@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {{name}}!"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.resource("config://app")
def get_config() -> str:
    """Return application configuration."""
    return "version: 0.1.0\\nenv: development"


@mcp.prompt()
def review_code(code: str) -> str:
    """Generate a code review prompt."""
    return f"Please review the following code and suggest improvements:\\n\\n{{code}}"


if __name__ == "__main__":
    mcp.run()
'''

PYPROJECT_TEMPLATE = '''\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "An MCP server built with FastMCP"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
]
'''

TEST_TEMPLATE = '''\
"""Basic tests for the MCP server."""

import pytest
from fastmcp import Client

from server import mcp


@pytest.fixture
def client():
    return Client(mcp)


@pytest.mark.asyncio
async def test_greet(client):
    result = await client.call_tool("greet", {{"name": "World"}})
    assert "Hello, World!" in str(result)


@pytest.mark.asyncio
async def test_add(client):
    result = await client.call_tool("add", {{"a": 2, "b": 3}})
    assert "5" in str(result)
'''

GITIGNORE_TEMPLATE = '''\
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.env
.pytest_cache/
.DS_Store
'''

README_TEMPLATE = '''\
# {name}

An MCP server built with [FastMCP](https://gofastmcp.com).

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run the server (stdio transport)
python server.py

# Or use FastMCP CLI
fastmcp run server.py

# Inspect with mcptools
mcptools inspect server.py

# Test interactively
mcptools test server.py

# Validate against best practices
mcptools validate server.py
```

## Tools

| Tool | Description |
|------|-------------|
| `greet` | Greet someone by name |
| `add` | Add two numbers together |

## Development

```bash
pip install -e ".[dev]"
pytest
```
'''


def run_init(name: str):
    project_dir = Path(name)

    if project_dir.exists():
        console.print(f"[red]Directory '{name}' already exists.[/]")
        raise SystemExit(1)

    project_dir.mkdir(parents=True)
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()

    files = {
        "server.py": SERVER_TEMPLATE.format(name=name),
        "pyproject.toml": PYPROJECT_TEMPLATE.format(name=name),
        "tests/test_server.py": TEST_TEMPLATE.format(name=name),
        ".gitignore": GITIGNORE_TEMPLATE,
        "README.md": README_TEMPLATE.format(name=name),
    }

    for filepath, content in files.items():
        (project_dir / filepath).write_text(content)

    os.system(f"cd {project_dir} && git init -q")

    console.print()
    console.print(f"  [green bold]Created[/] [cyan]{name}/[/]")
    console.print()
    console.print(f"    [dim]server.py[/]              MCP server with example tools")
    console.print(f"    [dim]pyproject.toml[/]         Project config")
    console.print(f"    [dim]tests/test_server.py[/]   Tests using FastMCP Client")
    console.print(f"    [dim]README.md[/]              Documentation")
    console.print()
    console.print("  [bold]Next steps:[/]")
    console.print()
    console.print(f"    cd {name}")
    console.print(f"    pip install -e .")
    console.print(f"    mcptools inspect server.py")
    console.print(f"    mcptools test server.py")
    console.print()
