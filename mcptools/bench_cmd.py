"""Benchmark MCP server tool response times."""

import asyncio
import json
import statistics
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import MCPClient, parse_server_spec

console = Console()


async def _bench_tool(client, tool_name, arguments, runs):
    times = []
    errors = 0
    for _ in range(runs):
        start = time.perf_counter()
        try:
            await client.call_tool(tool_name, arguments)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        except Exception:
            errors += 1
    return times, errors


def run_bench(
    server: str,
    tool: str = None,
    params: str = None,
    runs: int = 10,
):
    asyncio.run(_run_bench(server, tool, params, runs))


async def _run_bench(server, tool, params, runs):
    command, args = parse_server_spec(server)
    client = MCPClient()

    try:
        console.print(f"\n[dim]Connecting to[/] [cyan]{server}[/][dim]...[/]")
        await client.connect(command, args)
        tools = await client.list_tools()

        if not tools:
            console.print("[yellow]No tools found.[/]")
            return

        if tool:
            targets = [t for t in tools if t["name"] == tool]
            if not targets:
                names = ", ".join(t["name"] for t in tools)
                console.print(
                    f"[red]Tool '{tool}' not found.[/]\n"
                    f"[dim]Available: {names}[/]"
                )
                return
        else:
            targets = tools

        parsed_params = {}
        if params:
            try:
                parsed_params = json.loads(params)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON in --params:[/] {e}")
                return

        console.print(
            f"[dim]Benchmarking {len(targets)} tool(s) \u00d7 {runs} runs...[/]\n"
        )

        table = Table(
            title=f"Benchmark Results ({runs} runs)",
            border_style="blue",
            show_lines=True,
        )
        table.add_column("Tool", style="cyan bold", min_width=20)
        table.add_column("Avg", justify="right", style="white")
        table.add_column("Min", justify="right", style="green")
        table.add_column("Max", justify="right", style="red")
        table.add_column("P50", justify="right", style="dim")
        table.add_column("P95", justify="right", style="dim")
        table.add_column("Errors", justify="right")

        for t in targets:
            tool_name = t["name"]
            tool_params = parsed_params if tool else _default_params(t)

            times, errors = await _bench_tool(
                client, tool_name, tool_params, runs
            )

            if times:
                avg = statistics.mean(times)
                mn = min(times)
                mx = max(times)
                p50 = statistics.median(times)
                sorted_times = sorted(times)
                p95_idx = max(0, int(len(sorted_times) * 0.95) - 1)
                p95 = sorted_times[p95_idx]

                err_str = (
                    f"[red]{errors}[/]" if errors
                    else "[green]0[/]"
                )

                table.add_row(
                    tool_name,
                    f"{avg:.1f}ms",
                    f"{mn:.1f}ms",
                    f"{mx:.1f}ms",
                    f"{p50:.1f}ms",
                    f"{p95:.1f}ms",
                    err_str,
                )
            else:
                table.add_row(
                    tool_name, "\u2014", "\u2014", "\u2014", "\u2014", "\u2014",
                    f"[red]{errors}[/]",
                )

        console.print(table)
        console.print()

    finally:
        await client.close()


def _default_params(tool):
    """Generate minimal valid params for a tool based on its schema."""
    schema = tool.get("inputSchema", {})
    props = schema.get("properties", {})
    required = schema.get("required", [])

    params = {}
    for pname in required:
        pschema = props.get(pname, {})
        ptype = pschema.get("type", "string")
        defaults = {
            "string": "test",
            "integer": 1,
            "number": 1.0,
            "boolean": True,
            "array": [],
            "object": {},
        }
        params[pname] = defaults.get(ptype, "test")
    return params
