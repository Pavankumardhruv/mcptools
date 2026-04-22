"""Inspect an MCP server's capabilities."""

import asyncio
import json

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .client import with_client

console = Console()


async def _inspect(client):
    tools = await client.list_tools()
    resources = []
    prompts = []
    try:
        resources = await client.list_resources()
    except Exception:
        pass
    try:
        prompts = await client.list_prompts()
    except Exception:
        pass
    return {
        "server_info": client.server_info,
        "tools": tools,
        "resources": resources,
        "prompts": prompts,
    }


def run_inspect(server: str, json_output: bool = False):
    result = asyncio.run(with_client(server, _inspect))

    if json_output:
        console.print(
            Syntax(json.dumps(result, indent=2), "json", theme="monokai")
        )
        return

    server_info = result["server_info"]
    tools = result["tools"]
    resources = result["resources"]
    prompts = result["prompts"]

    server_name = server_info.get("name", "Unknown")
    server_version = server_info.get("version", "?")

    console.print()
    console.print(
        Panel(
            f"[bold cyan]{server_name}[/] v{server_version}\n\n"
            f"[bold]{len(tools)}[/] tools  ·  "
            f"[bold]{len(resources)}[/] resources  ·  "
            f"[bold]{len(prompts)}[/] prompts",
            title="Server Capabilities",
            border_style="blue",
        )
    )

    if tools:
        table = Table(title="Tools", border_style="blue", show_lines=True)
        table.add_column("Name", style="cyan bold", min_width=20)
        table.add_column("Description", style="white", ratio=2)
        table.add_column("Parameters", style="dim", ratio=1)

        for tool in tools:
            params = tool.get("inputSchema", {}).get("properties", {})
            required = tool.get("inputSchema", {}).get("required", [])
            param_lines = []
            for pname, pschema in params.items():
                ptype = pschema.get("type", "any")
                marker = " *" if pname in required else ""
                param_lines.append(f"{pname}: {ptype}{marker}")

            table.add_row(
                tool.get("name", "?"),
                tool.get("description", "[dim]No description[/]"),
                "\n".join(param_lines) if param_lines else "[dim]none[/]",
            )
        console.print(table)

    if resources:
        table = Table(title="Resources", border_style="green")
        table.add_column("URI", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Description", style="dim")
        table.add_column("MIME", style="dim")

        for res in resources:
            table.add_row(
                res.get("uri", "?"),
                res.get("name", "?"),
                res.get("description", "\u2014"),
                res.get("mimeType", "\u2014"),
            )
        console.print(table)

    if prompts:
        table = Table(title="Prompts", border_style="yellow")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Arguments", style="dim")

        for prompt in prompts:
            args = prompt.get("arguments", [])
            arg_strs = []
            for a in args:
                name = a.get("name", "?")
                if a.get("required"):
                    name += " *"
                arg_strs.append(name)

            table.add_row(
                prompt.get("name", "?"),
                prompt.get("description", "\u2014"),
                ", ".join(arg_strs) if arg_strs else "[dim]none[/]",
            )
        console.print(table)

    console.print()
