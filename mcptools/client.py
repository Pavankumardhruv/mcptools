"""Lightweight MCP client using JSON-RPC 2.0 over stdio."""

import asyncio
import json
import os


class MCPError(Exception):
    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP error {code}: {message}")


class MCPClient:
    def __init__(self):
        self.process = None
        self._id = 0
        self.server_info = None
        self.capabilities = None

    async def connect(self, command, args=None, env=None):
        merged_env = {**os.environ, **(env or {})}
        self.process = await asyncio.create_subprocess_exec(
            command,
            *(args or []),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env,
        )
        result = await self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcptools", "version": "0.1.0"},
            },
        )
        self.server_info = result.get("serverInfo", {})
        self.capabilities = result.get("capabilities", {})
        await self._notify("notifications/initialized")
        return result

    async def _request(self, method, params=None):
        self._id += 1
        request_id = self._id
        msg = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            msg["params"] = params
        await self._send(msg)
        return await self._read_response(request_id)

    async def _notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        await self._send(msg)

    async def _send(self, msg):
        line = json.dumps(msg) + "\n"
        self.process.stdin.write(line.encode())
        await self.process.stdin.drain()

    async def _read_response(self, expected_id):
        while True:
            try:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(), timeout=30
                )
            except asyncio.TimeoutError:
                raise ConnectionError("Server did not respond within 30 seconds")
            if not line:
                stderr_output = ""
                try:
                    stderr_output = (await self.process.stderr.read()).decode()
                except Exception:
                    pass
                raise ConnectionError(
                    f"Server process exited unexpectedly.\n{stderr_output}"
                )
            text = line.decode().strip()
            if not text:
                continue
            try:
                msg = json.loads(text)
            except json.JSONDecodeError:
                continue
            if "id" not in msg:
                continue
            if msg["id"] == expected_id:
                if "error" in msg:
                    err = msg["error"]
                    raise MCPError(
                        err.get("code", -1),
                        err.get("message", "Unknown error"),
                        err.get("data"),
                    )
                return msg.get("result", {})

    async def list_tools(self):
        result = await self._request("tools/list")
        return result.get("tools", [])

    async def list_resources(self):
        result = await self._request("resources/list")
        return result.get("resources", [])

    async def list_prompts(self):
        result = await self._request("prompts/list")
        return result.get("prompts", [])

    async def call_tool(self, name, arguments=None):
        return await self._request(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )

    async def close(self):
        if self.process:
            try:
                self.process.stdin.close()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except (asyncio.TimeoutError, ProcessLookupError):
                self.process.kill()


def parse_server_spec(spec):
    """Parse a server specification into (command, args).

    Supports:
      server.py           -> ("python", ["server.py"])
      server.js           -> ("node", ["server.js"])
      "python server.py"  -> ("python", ["server.py"])
    """
    spec = spec.strip()
    if spec.endswith(".py"):
        return "python", [spec]
    if spec.endswith(".js") or spec.endswith(".ts"):
        return "node", [spec]
    parts = spec.split()
    return parts[0], parts[1:]


async def with_client(server_spec, callback):
    """Connect to an MCP server, run callback with session, disconnect."""
    command, args = parse_server_spec(server_spec)
    client = MCPClient()
    try:
        await client.connect(command, args)
        return await callback(client)
    finally:
        await client.close()
