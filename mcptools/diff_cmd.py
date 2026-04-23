"""Compare capabilities of two MCP servers."""

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import with_client
from .utils import fetch_capabilities

console = Console()


def _tool_signature(tool):
    props = tool.get("inputSchema", {}).get("properties", {})
    required = tool.get("inputSchema", {}).get("required", [])
    params = []
    for pname, pschema in sorted(props.items()):
        ptype = pschema.get("type", "any")
        req = "*" if pname in required else ""
        params.append(f"{pname}{req}:{ptype}")
    return ",".join(params)


def _resource_signature(res):
    return f"{res.get('mimeType', '')}|{res.get('description', '')}"


def _prompt_signature(prompt):
    args = prompt.get("arguments", [])
    return ",".join(
        f"{a.get('name', '')}{'*' if a.get('required') else ''}"
        for a in args
    )


def run_diff(server_a: str, server_b: str):
    result_a = asyncio.run(with_client(server_a, fetch_capabilities))
    result_b = asyncio.run(with_client(server_b, fetch_capabilities))

    name_a = result_a["server_info"].get("name", server_a)
    name_b = result_b["server_info"].get("name", server_b)

    console.print()
    console.print(
        Panel(
            f"[cyan]{name_a}[/]  vs  [cyan]{name_b}[/]",
            title="Server Diff",
            border_style="blue",
        )
    )

    has_changes = False

    # Tools diff
    tools_a = {t["name"]: t for t in result_a["tools"]}
    tools_b = {t["name"]: t for t in result_b["tools"]}
    all_tools = sorted(set(tools_a.keys()) | set(tools_b.keys()))

    if all_tools:
        table = Table(title="Tools", border_style="blue", show_lines=True)
        table.add_column("Tool", style="bold", min_width=20)
        table.add_column("Status", justify="center", min_width=10)
        table.add_column("Details", ratio=2)

        for name in all_tools:
            in_a = name in tools_a
            in_b = name in tools_b

            if in_a and not in_b:
                table.add_row(name, "[red]REMOVED[/]", f"Was in {name_a}")
                has_changes = True
            elif not in_a and in_b:
                desc = tools_b[name].get("description", "")
                table.add_row(name, "[green]ADDED[/]", desc)
                has_changes = True
            else:
                sig_a = _tool_signature(tools_a[name])
                sig_b = _tool_signature(tools_b[name])
                desc_a = tools_a[name].get("description", "")
                desc_b = tools_b[name].get("description", "")

                changes = []
                if sig_a != sig_b:
                    changes.append(f"params: {sig_a} \u2192 {sig_b}")
                if desc_a != desc_b:
                    changes.append("description changed")

                if changes:
                    table.add_row(
                        name, "[yellow]CHANGED[/]", "\n".join(changes)
                    )
                    has_changes = True

        console.print(table)

    # Resources diff
    res_a = {r.get("uri", ""): r for r in result_a["resources"]}
    res_b = {r.get("uri", ""): r for r in result_b["resources"]}
    all_res = sorted(set(res_a.keys()) | set(res_b.keys()))

    if all_res:
        table = Table(title="Resources", border_style="green", show_lines=True)
        table.add_column("URI", style="bold", min_width=20)
        table.add_column("Status", justify="center", min_width=10)
        table.add_column("Details", ratio=2)

        for uri in all_res:
            in_a = uri in res_a
            in_b = uri in res_b
            if in_a and not in_b:
                table.add_row(uri, "[red]REMOVED[/]", "")
                has_changes = True
            elif not in_a and in_b:
                table.add_row(uri, "[green]ADDED[/]", "")
                has_changes = True
            else:
                if _resource_signature(res_a[uri]) != _resource_signature(res_b[uri]):
                    table.add_row(uri, "[yellow]CHANGED[/]", "metadata changed")
                    has_changes = True

        console.print(table)

    # Prompts diff
    pr_a = {p.get("name", ""): p for p in result_a["prompts"]}
    pr_b = {p.get("name", ""): p for p in result_b["prompts"]}
    all_pr = sorted(set(pr_a.keys()) | set(pr_b.keys()))

    if all_pr:
        table = Table(title="Prompts", border_style="yellow", show_lines=True)
        table.add_column("Prompt", style="bold", min_width=20)
        table.add_column("Status", justify="center", min_width=10)
        table.add_column("Details", ratio=2)

        for name in all_pr:
            in_a = name in pr_a
            in_b = name in pr_b
            if in_a and not in_b:
                table.add_row(name, "[red]REMOVED[/]", "")
                has_changes = True
            elif not in_a and in_b:
                table.add_row(name, "[green]ADDED[/]", "")
                has_changes = True
            else:
                if _prompt_signature(pr_a[name]) != _prompt_signature(pr_b[name]):
                    table.add_row(name, "[yellow]CHANGED[/]", "arguments changed")
                    has_changes = True

        console.print(table)

    if not has_changes:
        console.print("\n[green]Servers are identical.[/]")

    # Summary
    t_added = len(set(tools_b) - set(tools_a))
    t_removed = len(set(tools_a) - set(tools_b))
    t_changed = sum(
        1 for n in set(tools_a) & set(tools_b)
        if _tool_signature(tools_a[n]) != _tool_signature(tools_b[n])
        or tools_a[n].get("description") != tools_b[n].get("description")
    )

    parts = []
    if t_added:
        parts.append(f"[green]+{t_added} added[/]")
    if t_removed:
        parts.append(f"[red]-{t_removed} removed[/]")
    if t_changed:
        parts.append(f"[yellow]~{t_changed} changed[/]")
    if not parts:
        parts.append("[green]no changes[/]")

    console.print(
        Panel(
            f"Tools: {' \u00b7 '.join(parts)}",
            title="Summary",
            border_style="blue",
        )
    )
    console.print()
