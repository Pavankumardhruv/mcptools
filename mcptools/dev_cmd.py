"""Run an MCP server in dev mode with auto-reload and live inspection."""

import asyncio
import os
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import with_client

console = Console()


def _collect_mtimes(directory, extensions=(".py", ".js", ".ts")):
    mtimes = {}
    for ext in extensions:
        for path in Path(directory).rglob(f"*{ext}"):
            if ".venv" in path.parts or "node_modules" in path.parts:
                continue
            try:
                mtimes[str(path)] = path.stat().st_mtime
            except OSError:
                pass
    return mtimes


def _find_changed(old, new):
    changed = []
    for f in new:
        if f not in old or new[f] != old[f]:
            changed.append(os.path.basename(f))
    for f in old:
        if f not in new:
            changed.append(f"{os.path.basename(f)} (deleted)")
    return changed


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


def _display(result):
    info = result["server_info"]
    tools = result["tools"]
    resources = result["resources"]
    prompts = result["prompts"]

    name = info.get("name", "Unknown")

    console.print(
        Panel(
            f"[bold cyan]{name}[/]\n\n"
            f"[bold]{len(tools)}[/] tools  ·  "
            f"[bold]{len(resources)}[/] resources  ·  "
            f"[bold]{len(prompts)}[/] prompts",
            border_style="blue",
        )
    )

    if tools:
        table = Table(border_style="blue", show_header=True, padding=(0, 1))
        table.add_column("Tool", style="cyan bold")
        table.add_column("Description", style="white")
        table.add_column("Params", style="dim")
        for tool in tools:
            params = tool.get("inputSchema", {}).get("properties", {})
            pnames = ", ".join(params.keys()) if params else "none"
            desc = tool.get("description", "")
            if len(desc) > 50:
                desc = desc[:47] + "..."
            table.add_row(tool["name"], desc, pnames)
        console.print(table)


def _diff_report(old, new):
    old_names = {t["name"] for t in old["tools"]}
    new_names = {t["name"] for t in new["tools"]}
    added = new_names - old_names
    removed = old_names - new_names
    parts = []
    if added:
        parts.append(f"[green]+{', '.join(added)}[/]")
    if removed:
        parts.append(f"[red]-{', '.join(removed)}[/]")
    if parts:
        console.print(f"  Tools: {' '.join(parts)}")


def run_dev(server: str):
    server_path = server.strip()
    if os.path.isfile(server_path):
        watch_dir = os.path.dirname(os.path.abspath(server_path)) or "."
    else:
        watch_dir = "."

    console.clear()
    console.print(
        f"[bold blue]mcptools dev[/] · watching [cyan]{watch_dir}[/] · Ctrl+C to stop\n"
    )

    try:
        result = asyncio.run(with_client(server, _inspect))
        _display(result)
    except Exception as e:
        console.print(f"[red]Failed to connect:[/] {e}")
        result = None

    console.print(f"\n[dim]Watching for changes...[/]")
    last_mtimes = _collect_mtimes(watch_dir)

    try:
        while True:
            time.sleep(1)
            current_mtimes = _collect_mtimes(watch_dir)
            changed = _find_changed(last_mtimes, current_mtimes)

            if changed:
                last_mtimes = current_mtimes
                console.print(
                    f"\n[yellow]Changed:[/] {', '.join(changed[:5])}"
                )
                console.print("[dim]Reloading...[/]\n")
                try:
                    new_result = asyncio.run(with_client(server, _inspect))
                    _display(new_result)
                    if result:
                        _diff_report(result, new_result)
                    result = new_result
                except Exception as e:
                    console.print(f"[red]Error:[/] {e}")
                console.print(f"\n[dim]Watching for changes...[/]")

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/]")
