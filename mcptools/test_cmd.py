"""Interactively test MCP server tools."""

import asyncio
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.syntax import Syntax

from .client import MCPClient, parse_server_spec

console = Console()


def run_test(server: str, tool_name: str = None, params: str = None):
    asyncio.run(_run_test(server, tool_name, params))


async def _run_test(server: str, tool_name: str = None, params: str = None):
    command, args = parse_server_spec(server)
    client = MCPClient()

    try:
        console.print(f"\n[dim]Connecting to[/] [cyan]{server}[/][dim]...[/]")
        await client.connect(command, args)
        tools = await client.list_tools()

        if not tools:
            console.print("[yellow]No tools found on this server.[/]")
            return

        if tool_name:
            matching = [t for t in tools if t["name"] == tool_name]
            if not matching:
                names = ", ".join(t["name"] for t in tools)
                console.print(
                    f"[red]Tool '{tool_name}' not found.[/]\n"
                    f"[dim]Available: {names}[/]"
                )
                sys.exit(1)

            parsed_params = {}
            if params:
                try:
                    parsed_params = json.loads(params)
                except json.JSONDecodeError as e:
                    console.print(
                        f"[red]Invalid JSON in --params:[/] {e}\n"
                        f'[dim]Example: --params \'{{"key": "value"}}\'[/]'
                    )
                    sys.exit(1)

            result = await client.call_tool(tool_name, parsed_params)
            _print_result(tool_name, result)
            return

        while True:
            console.print("\n[bold]Available tools:[/]\n")
            for i, tool in enumerate(tools, 1):
                desc = tool.get("description", "No description")
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                console.print(
                    f"  [cyan]{i:>3}[/]  {tool['name']:<30}  [dim]{desc}[/]"
                )

            console.print(f"\n  [dim]  0  Exit[/]")

            choice = IntPrompt.ask("\nSelect a tool", default=0)
            if choice == 0:
                break
            if choice < 1 or choice > len(tools):
                console.print("[red]Invalid selection[/]")
                continue

            tool = tools[choice - 1]
            arguments = _prompt_params(tool)

            console.print(
                f"\n[dim]Calling[/] [cyan]{tool['name']}[/][dim]...[/]"
            )
            result = await client.call_tool(tool["name"], arguments)
            _print_result(tool["name"], result)

    finally:
        await client.close()


def _prompt_params(tool):
    schema = tool.get("inputSchema", {})
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    if not properties:
        return {}

    console.print(
        f"\n[bold]Parameters for [cyan]{tool['name']}[/cyan]:[/]\n"
    )
    arguments = {}

    for name, prop in properties.items():
        ptype = prop.get("type", "string")
        desc = prop.get("description", "")
        is_required = name in required

        label = f"  {name} [dim]({ptype})[/dim]"
        if desc:
            label += f" [dim]— {desc}[/dim]"
        if not is_required:
            label += " [dim][optional][/dim]"

        while True:
            default = "" if not is_required else ...
            value = Prompt.ask(label, default=default)

            if value == "" and not is_required:
                break

            try:
                if ptype == "integer":
                    arguments[name] = int(value)
                elif ptype == "number":
                    arguments[name] = float(value)
                elif ptype == "boolean":
                    arguments[name] = value.lower() in (
                        "true", "1", "yes", "y", "on",
                    )
                elif ptype in ("object", "array"):
                    arguments[name] = json.loads(value)
                else:
                    arguments[name] = value
                break
            except (ValueError, json.JSONDecodeError) as e:
                console.print(f"  [red]Invalid {ptype}:[/] {e}")
                if ptype in ("object", "array"):
                    console.print(
                        f'  [dim]Example: {{"key": "value"}}[/]'
                    )

    return arguments


def _print_result(tool_name, result):
    content = result.get("content", [])
    is_error = result.get("isError", False)

    border = "red" if is_error else "green"
    title = f"{'Error' if is_error else 'Result'}: {tool_name}"

    parts = []
    for item in content:
        item_type = item.get("type")
        if item_type == "text":
            parts.append(item["text"])
        elif item_type == "image":
            parts.append(f"[dim][image: {item.get('mimeType', 'unknown')}][/dim]")
        else:
            parts.append(json.dumps(item, indent=2))

    output = "\n".join(parts) if parts else "[dim]Empty response[/dim]"

    try:
        parsed = json.loads(output)
        formatted = Syntax(
            json.dumps(parsed, indent=2), "json", theme="monokai"
        )
        console.print(Panel(formatted, title=title, border_style=border))
    except (json.JSONDecodeError, TypeError):
        console.print(Panel(output, title=title, border_style=border))
