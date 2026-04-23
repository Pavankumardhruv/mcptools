"""Run an MCP server in dev mode with auto-reload and live inspection."""

import asyncio
import os
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import with_client
from .utils import fetch_capabilities

console = Console()


def _collect_mtimes(directory, extensions=(".py", ".js", ".ts")):
    mtimes = {}
    skip = {".venv", "node_modules", "__pycache__", ".git"}
    for ext in extensions:
        for path in Path(directory).rglob(f"*{ext}"):
            if skip & set(path.parts):
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


def _display(result):
    info = result["server_info"]
    tools = result["tools"]
    resources = result["resources"]
    prompts = result["prompts"]

    name = info.get("name", "Unknown")

    console.print(
        Panel(
            f"[bold cyan]{name}[/]\n\n"
            f"[bold]{len(tools)}[/] tools  \u00b7  "
            f"[bold]{len(resources)}[/] resources  \u00b7  "
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
            table.add_row(tool.get("name", "?"), desc, pnames)
        console.print(table)


def _diff_report(old, new):
    old_names = {t["name"] for t in old["tools"]}
    new_names = {t["name"] for t in new["tools"]}
    added = new_names - old_names
    removed = old_names - new_names
    parts = []
    if added:
        parts.append(f"[green]+{', '.join(sorted(added))}[/]")
    if removed:
        parts.append(f"[red]-{', '.join(sorted(removed))}[/]")
    if not added and not removed:
        old_descs = {t["name"]: t.get("description") for t in old["tools"]}
        new_descs = {t["name"]: t.get("description") for t in new["tools"]}
        changed = [n for n in new_names if old_descs.get(n) != new_descs.get(n)]
        if changed:
            parts.append(f"[yellow]~{', '.join(sorted(changed))}[/]")
    if parts:
        console.print(f"  Tools: {' '.join(parts)}")
    else:
        console.print("  [dim]No changes to tools[/]")


def run_dev(server: str):
    server_path = server.strip()
    if os.path.isfile(server_path):
        watch_dir = os.path.dirname(os.path.abspath(server_path)) or "."
    else:
        watch_dir = "."

    console.clear()
    console.print(
        f"[bold blue]mcptools dev[/] \u00b7 watching [cyan]{watch_dir}[/] \u00b7 Ctrl+C to stop\n"
    )

    result = None
    try:
        result = asyncio.run(with_client(server, fetch_capabilities))
        _display(result)
        console.print("  [green]\u2713 Server OK[/]")
    except Exception as e:
        console.print(f"  [red]\u2717 Failed to connect:[/] {e}")

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
                    f"\n[yellow]\u21bb Changed:[/] {', '.join(changed[:5])}"
                )

                try:
                    new_result = asyncio.run(
                        with_client(server, fetch_capabilities)
                    )
                    _display(new_result)
                    if result:
                        _diff_report(result, new_result)
                    result = new_result
                    console.print("  [green]\u2713 Server OK[/]")
                except Exception as e:
                    console.print(f"  [red]\u2717 Error:[/] {e}")

                console.print(f"\n[dim]Watching for changes...[/]")

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/]")
