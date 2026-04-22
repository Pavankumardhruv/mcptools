"""Validate an MCP server against best practices."""

import asyncio
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import with_client

console = Console()

VERB_PREFIXES = {
    "get", "list", "create", "update", "delete", "remove", "add", "set",
    "search", "find", "fetch", "retrieve", "check", "validate", "run",
    "execute", "send", "read", "write", "upload", "download", "convert",
    "generate", "analyze", "calculate", "process", "start", "stop",
    "enable", "disable", "connect", "disconnect", "subscribe", "unsubscribe",
    "export", "import", "sync", "query", "count", "move", "copy", "rename",
    "open", "close", "build", "deploy", "test", "parse", "format", "sort",
    "filter", "merge", "split", "extract", "transform", "load", "save",
    "reset", "clear", "init", "configure", "register", "unregister",
    "publish", "approve", "reject", "cancel", "retry", "schedule",
}


class Check:
    def __init__(self, name):
        self.name = name
        self.passed = 0
        self.warnings = 0
        self.failures = 0
        self.messages = []

    def ok(self, msg=None):
        self.passed += 1
        if msg:
            self.messages.append(("pass", msg))

    def warn(self, msg):
        self.warnings += 1
        self.messages.append(("warn", msg))

    def fail(self, msg):
        self.failures += 1
        self.messages.append(("fail", msg))

    @property
    def status(self):
        if self.failures:
            return "fail"
        if self.warnings:
            return "warn"
        return "pass"


def _check_tool_naming(tools):
    c = Check("Tool Naming")
    for tool in tools:
        name = tool.get("name", "")
        if not re.match(r"^[a-z][a-z0-9_]*$", name):
            c.fail(f"'{name}' \u2014 should be snake_case")
        elif not any(name.startswith(v) for v in VERB_PREFIXES):
            c.warn(
                f"'{name}' \u2014 consider starting with a verb "
                "(get_, create_, list_, ...)"
            )
        else:
            c.ok()
    if not tools:
        c.warn("No tools found")
    return c


def _check_tool_descriptions(tools):
    c = Check("Tool Descriptions")
    for tool in tools:
        name = tool.get("name", "")
        desc = tool.get("description", "")
        if not desc:
            c.fail(f"'{name}' \u2014 missing description")
        elif len(desc) < 10:
            c.warn(f"'{name}' \u2014 description too short ({len(desc)} chars)")
        elif len(desc) > 500:
            c.warn(f"'{name}' \u2014 description very long ({len(desc)} chars)")
        else:
            c.ok()
    return c


def _check_param_schemas(tools):
    c = Check("Parameter Schemas")
    for tool in tools:
        name = tool.get("name", "")
        schema = tool.get("inputSchema", {})
        props = schema.get("properties", {})
        if not props:
            continue
        for pname, pschema in props.items():
            if "type" not in pschema:
                c.fail(f"'{name}.{pname}' \u2014 missing type annotation")
            elif "description" not in pschema:
                c.warn(f"'{name}.{pname}' \u2014 no description")
            else:
                c.ok()
    return c


def _check_uniqueness(tools, resources, prompts):
    c = Check("Uniqueness")
    seen = set()
    for tool in tools:
        name = tool.get("name", "")
        if name in seen:
            c.fail(f"Duplicate tool: '{name}'")
        else:
            seen.add(name)
            c.ok()
    seen_uris = set()
    for res in resources:
        uri = res.get("uri", "")
        if uri in seen_uris:
            c.fail(f"Duplicate resource URI: '{uri}'")
        else:
            seen_uris.add(uri)
            c.ok()
    return c


def _check_tool_count(tools):
    c = Check("Tool Count")
    n = len(tools)
    if n > 30:
        c.fail(f"{n} tools \u2014 too many, causes context bloat. Split into servers.")
    elif n > 20:
        c.warn(f"{n} tools \u2014 getting high, may cause context bloat")
    elif n == 0:
        c.warn("No tools found")
    else:
        c.ok(f"{n} tools")
    return c


def _check_prompt_descriptions(prompts):
    c = Check("Prompt Descriptions")
    for prompt in prompts:
        name = prompt.get("name", "")
        desc = prompt.get("description", "")
        if not desc:
            c.warn(f"'{name}' \u2014 missing description")
        else:
            c.ok()
    if not prompts:
        c.ok("No prompts to check")
    return c


async def _fetch_server_data(client):
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
    return tools, resources, prompts


def run_validate(server: str):
    tools, resources, prompts = asyncio.run(
        with_client(server, _fetch_server_data)
    )

    checks = [
        _check_tool_naming(tools),
        _check_tool_descriptions(tools),
        _check_param_schemas(tools),
        _check_uniqueness(tools, resources, prompts),
        _check_tool_count(tools),
        _check_prompt_descriptions(prompts),
    ]

    console.print()
    table = Table(
        title="Validation Results", border_style="blue", show_lines=True
    )
    table.add_column("Check", style="bold", min_width=20)
    table.add_column("Status", justify="center", min_width=8)
    table.add_column("Details", ratio=2)

    total_pass = 0
    total_warn = 0
    total_fail = 0

    status_label = {
        "pass": "[green]PASS[/]",
        "warn": "[yellow]WARN[/]",
        "fail": "[red]FAIL[/]",
    }
    icons = {"pass": "\u2713", "warn": "\u26a0", "fail": "\u2717"}
    colors = {"pass": "green", "warn": "yellow", "fail": "red"}

    for check in checks:
        total_pass += check.passed
        total_warn += check.warnings
        total_fail += check.failures

        lines = []
        for level, msg in check.messages:
            lines.append(f"[{colors[level]}]{icons[level]}[/] {msg}")

        table.add_row(
            check.name,
            status_label[check.status],
            "\n".join(lines) if lines else "[green]All checks passed[/]",
        )

    console.print(table)

    total = total_pass + total_warn + total_fail
    score = int((total_pass / total) * 100) if total > 0 else 100

    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellow"
    else:
        color = "red"

    console.print(
        Panel(
            f"[{color} bold]{score}/100[/]  \u00b7  "
            f"[green]{total_pass} passed[/]  \u00b7  "
            f"[yellow]{total_warn} warnings[/]  \u00b7  "
            f"[red]{total_fail} failures[/]",
            title="Score",
            border_style=color,
        )
    )
    console.print()
