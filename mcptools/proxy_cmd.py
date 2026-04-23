"""MCP traffic proxy — sit between client and server, log all JSON-RPC messages."""

import asyncio
import json
import os
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .client import parse_server_spec

console = Console(stderr=True)


class MCPProxy:
    """Transparent proxy that forwards JSON-RPC between stdin/stdout and a server."""

    def __init__(self, command, args):
        self.command = command
        self.args = args
        self.process = None
        self.msg_count = 0
        self.start_time = None

    async def start(self):
        self.start_time = time.monotonic()
        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        console.print(
            Panel(
                f"[cyan]{self.command} {' '.join(self.args)}[/]\n"
                f"[dim]Forwarding stdin/stdout \u00b7 Ctrl+C to stop[/]",
                title="[bold]mcptools proxy[/]",
                border_style="blue",
            )
        )

        await asyncio.gather(
            self._forward_client_to_server(),
            self._forward_server_to_client(),
            self._forward_stderr(),
        )

    async def _forward_client_to_server(self):
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin.buffer
        )

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                self._log_message(line, direction="client \u2192 server")
                self.process.stdin.write(line)
                await self.process.stdin.drain()
        except (asyncio.CancelledError, ConnectionError):
            pass

    async def _forward_server_to_client(self):
        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                self._log_message(line, direction="server \u2192 client")
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
        except (asyncio.CancelledError, ConnectionError):
            pass

    async def _forward_stderr(self):
        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                console.print(f"[dim]stderr: {line.decode().rstrip()}[/]")
        except (asyncio.CancelledError, ConnectionError):
            pass

    def _log_message(self, raw, direction):
        self.msg_count += 1
        elapsed = time.monotonic() - self.start_time
        text = raw.decode().strip()

        try:
            msg = json.loads(text)
            method = msg.get("method", "")
            msg_id = msg.get("id", "")
            is_response = "result" in msg or "error" in msg
            is_error = "error" in msg

            if is_response:
                label = f"[{'red' if is_error else 'green'}]response[/]"
                if msg_id:
                    label += f" id={msg_id}"
                if is_error:
                    err = msg["error"]
                    label += f" [red]{err.get('message', '')}[/]"
            elif method:
                label = f"[cyan]{method}[/]"
                if msg_id:
                    label += f" [dim]id={msg_id}[/]"
            else:
                label = "[dim]message[/]"

            header = (
                f"[dim]#{self.msg_count} {elapsed:>6.2f}s[/]  "
                f"{direction}  {label}"
            )
            console.print(header)

            formatted = json.dumps(msg, indent=2)
            if len(formatted) < 500:
                console.print(
                    Syntax(formatted, "json", theme="monokai", padding=1)
                )
            else:
                short = json.dumps(msg, indent=2)[:400] + "\n  ..."
                console.print(
                    Syntax(short, "json", theme="monokai", padding=1)
                )

        except json.JSONDecodeError:
            console.print(
                f"[dim]#{self.msg_count} {elapsed:>6.2f}s[/]  "
                f"{direction}  [dim]{text[:100]}[/]"
            )

        console.print()


def run_proxy(server: str):
    command, args = parse_server_spec(server)

    try:
        asyncio.run(MCPProxy(command, args).start())
    except KeyboardInterrupt:
        console.print("\n[dim]Proxy stopped.[/]")
