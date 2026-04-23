"""Scaffold a new MCP server project."""

import subprocess
from pathlib import Path

from rich.console import Console

console = Console()

TEMPLATES = {
    "basic": {
        "description": "Simple server with example tools",
        "server": '''\
from fastmcp import FastMCP

mcp = FastMCP("{name}")


@mcp.tool()
def get_greeting(name: str) -> str:
    """Generate a personalized greeting message for the given name."""
    return f"Hello, {{name}}!"


@mcp.tool()
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers and return the result."""
    return a + b


@mcp.resource("config://app")
def get_config() -> str:
    """Return the current application configuration as a YAML string."""
    return "version: 0.1.0\\nenv: development"


@mcp.prompt()
def review_code(code: str) -> str:
    """Generate a prompt that asks for a thorough code review with suggestions."""
    return f"Please review the following code and suggest improvements:\\n\\n{{code}}"


if __name__ == "__main__":
    mcp.run()
''',
    },
    "api": {
        "description": "Server that wraps an external REST API",
        "server": '''\
import os

import httpx
from fastmcp import FastMCP

mcp = FastMCP("{name}")

BASE_URL = os.getenv("{name_upper}_API_URL", "https://jsonplaceholder.typicode.com")


@mcp.tool()
def list_items(limit: int = 10) -> str:
    """Fetch a list of items from the API, limited to the specified count."""
    with httpx.Client() as client:
        resp = client.get(f"{{BASE_URL}}/posts", params={{"_limit": limit}})
        resp.raise_for_status()
        items = resp.json()
    lines = [f"- [{{item['id']}}] {{item['title']}}" for item in items]
    return "\\n".join(lines)


@mcp.tool()
def get_item(item_id: int) -> str:
    """Retrieve a single item by its ID from the API."""
    with httpx.Client() as client:
        resp = client.get(f"{{BASE_URL}}/posts/{{item_id}}")
        resp.raise_for_status()
        item = resp.json()
    return f"# {{item['title']}}\\n\\n{{item['body']}}"


@mcp.tool()
def search_items(query: str) -> str:
    """Search items by title, returning all matches for the given query string."""
    with httpx.Client() as client:
        resp = client.get(f"{{BASE_URL}}/posts")
        resp.raise_for_status()
        items = resp.json()
    matches = [i for i in items if query.lower() in i["title"].lower()]
    if not matches:
        return f"No items matching '{{query}}'"
    lines = [f"- [{{m['id']}}] {{m['title']}}" for m in matches]
    return "\\n".join(lines)


if __name__ == "__main__":
    mcp.run()
''',
    },
    "database": {
        "description": "Server with SQLite database access",
        "server": '''\
import sqlite3
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("{name}")

DB_PATH = Path(__file__).parent / "data.db"


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS items "
        "(id INTEGER PRIMARY KEY, name TEXT NOT NULL, status TEXT DEFAULT 'active')"
    )
    conn.commit()
    return conn


@mcp.tool()
def list_records(status: str = "active") -> str:
    """List all database records, optionally filtered by status (active/archived)."""
    conn = _get_db()
    rows = conn.execute("SELECT * FROM items WHERE status = ?", (status,)).fetchall()
    conn.close()
    if not rows:
        return f"No records with status '{{status}}'"
    lines = [f"- [{{r['id']}}] {{r['name']}} ({{r['status']}})" for r in rows]
    return "\\n".join(lines)


@mcp.tool()
def create_record(name: str) -> str:
    """Create a new record with the given name and return its assigned ID."""
    conn = _get_db()
    cursor = conn.execute("INSERT INTO items (name) VALUES (?)", (name,))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return f"Created record #{{record_id}}: {{name}}"


@mcp.tool()
def update_record(record_id: int, name: str = "", status: str = "") -> str:
    """Update an existing record's name or status by its ID."""
    conn = _get_db()
    parts, values = [], []
    if name:
        parts.append("name = ?")
        values.append(name)
    if status:
        parts.append("status = ?")
        values.append(status)
    if not parts:
        return "Nothing to update"
    values.append(record_id)
    conn.execute(f"UPDATE items SET {{', '.join(parts)}} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return f"Updated record #{{record_id}}"


@mcp.tool()
def delete_record(record_id: int) -> str:
    """Permanently delete a record by its ID from the database."""
    conn = _get_db()
    conn.execute("DELETE FROM items WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return f"Deleted record #{{record_id}}"


if __name__ == "__main__":
    mcp.run()
''',
    },
}


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
    "fastmcp>=2.0.0",{extra_deps}
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
]
'''

TEST_TEMPLATE = '''\
"""Tests for the MCP server."""

import pytest
from fastmcp import Client

from server import mcp


@pytest.fixture
def client():
    return Client(mcp)


@pytest.mark.asyncio
async def test_tools_exist(client):
    tools = await client.list_tools()
    assert len(tools) > 0, "Server should expose at least one tool"
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
*.db
'''

README_TEMPLATE = '''\
# {name}

An MCP server built with [FastMCP](https://gofastmcp.com).

## Quick Start

```bash
pip install -e .
python server.py
```

## Development

```bash
pip install -e ".[dev]"

mcptools inspect server.py     # View tools, resources, prompts
mcptools test server.py        # Test tools interactively
mcptools validate server.py    # Lint against best practices
mcptools dev server.py         # Auto-reload on changes
mcptools docs server.py        # Generate documentation
```
'''


def run_init(name: str, template: str = "basic"):
    project_dir = Path(name)

    if project_dir.exists():
        console.print(f"[red]Directory '{name}' already exists.[/]")
        raise SystemExit(1)

    if template not in TEMPLATES:
        console.print(
            f"[red]Unknown template '{template}'. "
            f"Available: {', '.join(TEMPLATES.keys())}[/]"
        )
        raise SystemExit(1)

    tmpl = TEMPLATES[template]

    project_dir.mkdir(parents=True)
    (project_dir / "tests").mkdir()

    extra_deps = ""
    if template == "api":
        extra_deps = '\n    "httpx>=0.27.0",'

    name_upper = name.upper().replace("-", "_")

    files = {
        "server.py": tmpl["server"].format(name=name, name_upper=name_upper),
        "pyproject.toml": PYPROJECT_TEMPLATE.format(name=name, extra_deps=extra_deps),
        "tests/test_server.py": TEST_TEMPLATE,
        ".gitignore": GITIGNORE_TEMPLATE,
        "README.md": README_TEMPLATE.format(name=name),
    }

    for filepath, content in files.items():
        (project_dir / filepath).write_text(content)

    subprocess.run(
        ["git", "init", "-q"], cwd=str(project_dir),
        capture_output=True, check=False,
    )

    console.print()
    console.print(f"  [green bold]Created[/] [cyan]{name}/[/] [dim]({template} template)[/]")
    console.print()
    console.print(f"    [dim]server.py[/]              {tmpl['description']}")
    console.print(f"    [dim]pyproject.toml[/]         Project config")
    console.print(f"    [dim]tests/test_server.py[/]   Test scaffold")
    console.print(f"    [dim]README.md[/]              Documentation")
    console.print()
    console.print("  [bold]Next steps:[/]")
    console.print()
    console.print(f"    cd {name}")
    console.print(f"    pip install -e .")
    console.print(f"    mcptools dev server.py")
    console.print()
