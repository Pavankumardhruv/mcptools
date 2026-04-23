<p align="center">
  <h1 align="center">mcptools</h1>
</p>

<p align="center">
  <strong>The Swiss Army knife for MCP server development.</strong><br>
  Scaffold. Inspect. Test. Validate. Debug. Benchmark. Ship.
</p>

<p align="center">
  <a href="https://github.com/Pavankumardhruv/mcptools/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Pavankumardhruv/mcptools?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/protocol-MCP-purple?style=flat-square" alt="MCP">
</p>

---

Building MCP servers is easy. Building them **well** is harder. mcptools gives you a complete development toolkit — from scaffolding to production validation — so you can ship MCP servers with confidence.

**Zero dependencies on the MCP SDK.** mcptools connects to any MCP server over stdio using the JSON-RPC protocol directly. Works with Python, Node.js, Go, Rust — anything that speaks MCP.

## Demo

```bash
$ mcptools init my-server
  Created my-server/ (basic template)
    server.py, pyproject.toml, tests/, README.md

$ mcptools inspect my-server/server.py
╭──────── Server Capabilities ────────╮
│ my-server v3.2.4                    │
│ 2 tools  ·  1 resources  ·  1 prom │
╰─────────────────────────────────────╯
┌──────────────── Tools ─────────────────┐
│ Name            │ Description  │ Params│
├─────────────────┼──────────────┼───────┤
│ get_greeting    │ Generate a   │ name  │
│                 │ greeting...  │       │
│ calculate_sum   │ Calculate    │ a, b  │
│                 │ the sum...   │       │
└─────────────────┴──────────────┴───────┘

$ mcptools test my-server/server.py --tool get_greeting --params '{"name": "World"}'
╭──── Result: get_greeting ────╮
│ Hello, World!                │
╰──────────────────────────────╯

$ mcptools validate my-server/server.py
┌────────────── Validation ──────────────┐
│ Tool Naming        │  PASS  │ ✓ ✓     │
│ Tool Descriptions  │  PASS  │ ✓ ✓     │
│ Parameter Schemas  │  WARN  │ ⚠ no... │
│ Security Hints     │  PASS  │ ✓       │
└────────────────────┴────────┴─────────┘
╭── Score ──╮
│  77/100   │
╰───────────╯

$ mcptools bench my-server/server.py --runs 10
┌────────── Benchmark (10 runs) ──────────┐
│ Tool            │  Avg │  P50 │  P95    │
├─────────────────┼──────┼──────┼─────────┤
│ get_greeting    │ 0.8ms│ 0.6ms│ 1.2ms  │
│ calculate_sum   │ 0.6ms│ 0.5ms│ 0.7ms  │
└─────────────────┴──────┴──────┴─────────┘

$ mcptools diff server_v1.py server_v2.py
┌──────── Server Diff ────────┐
│ add_item      │   ADDED     │
│ get_items     │   CHANGED   │
│ old_tool      │   REMOVED   │
└───────────────┴─────────────┘
Summary: +1 added · ~1 changed · -1 removed
```

## Install

```bash
pip install git+https://github.com/Pavankumardhruv/mcptools.git
```

Or clone locally:

```bash
git clone https://github.com/Pavankumardhruv/mcptools.git
cd mcptools
pip install -e .
```

## Commands

### `mcptools init <name>` — Scaffold

Create a new MCP server project with [FastMCP](https://gofastmcp.com).

```bash
mcptools init my-server                    # Basic template
mcptools init my-server --template api     # REST API wrapper
mcptools init my-server --template database # SQLite CRUD server
```

**Templates:**

| Template | What you get |
|----------|-------------|
| `basic` | Greeting + math tools, resource, prompt |
| `api` | httpx-based REST API wrapper with list/get/search |
| `database` | SQLite CRUD operations (list, create, update, delete) |

Each template includes `pyproject.toml`, tests, `.gitignore`, and a git repo.

### `mcptools inspect <server>` — Explore

Connect to any MCP server and display its capabilities.

```bash
mcptools inspect server.py              # Python server
mcptools inspect server.js              # Node.js server
mcptools inspect "python server.py"     # Explicit command
mcptools inspect server.py --json       # Raw JSON output (pipe to jq)
```

### `mcptools test <server>` — Test

Interactively test tools or script them for CI.

```bash
mcptools test server.py                                      # Interactive
mcptools test server.py --tool get_greeting --params '{"name": "World"}'  # Scripted
```

Interactive mode shows all tools, lets you pick one, prompts for parameters with type validation, and displays results.

### `mcptools validate <server>` — Lint

Validate against MCP best practices. 8 checks across naming, descriptions, schemas, security, and more.

```bash
mcptools validate server.py                  # Full report
mcptools validate server.py --min-score 80   # Fail if below 80 (for CI)
```

**Checks:**

| Check | What it validates |
|---|---|
| Tool Naming | snake_case, starts with a verb |
| Tool Descriptions | Present, 10–500 characters |
| Parameter Schemas | Type annotations and descriptions |
| Uniqueness | No duplicate tools, resources, or prompts |
| Tool Count | Warns at 20+, fails at 30+ |
| Resource Quality | URIs, descriptions, MIME types |
| Prompt Quality | Descriptions and argument docs |
| Security Hints | Flags dangerous operations, credential exposure, raw SQL |

### `mcptools dev <server>` — Develop

Watch for file changes, auto-reconnect, and show updated capabilities with a diff.

```bash
mcptools dev server.py
```

```
mcptools dev · watching /project · Ctrl+C to stop

╭── my-server ──────────────────╮
│ 2 tools · 1 resources · 1 pr │
╰───────────────────────────────╯

✓ Server OK

Watching for changes...

↻ Changed: server.py
  Tools: +search_items
  ✓ Server OK
```

### `mcptools docs <server>` — Document

Auto-generate Markdown documentation from a live server.

```bash
mcptools docs server.py                  # Print to stdout
mcptools docs server.py -o TOOLS.md      # Write to file
```

Generates tool tables, parameter schemas, resource URIs, and prompt arguments. Ready to paste into your README.

### `mcptools proxy <server>` — Debug

Transparent traffic proxy. Sit between any MCP client and server, log every JSON-RPC message with timestamps and formatting.

```bash
mcptools proxy server.py
```

```
╭── mcptools proxy ──────────────────────╮
│ python server.py                       │
│ Forwarding stdin/stdout · Ctrl+C to stop│
╰────────────────────────────────────────╯

#1  0.01s  client → server  initialize id=1
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  ...
}

#2  0.03s  server → client  response id=1
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "serverInfo": ... }
}
```

Use this to debug protocol issues, inspect what your client is actually sending, or understand an unfamiliar server's behavior.

### `mcptools diff <server_a> <server_b>` — Compare

Compare capabilities of two MCP servers side by side. Essential for versioning and migration.

```bash
mcptools diff server_v1.py server_v2.py
mcptools diff old_server.py new_server.py
```

Shows added, removed, and changed tools, resources, and prompts with a summary.

### `mcptools bench <server>` — Benchmark

Measure tool response times with statistical analysis.

```bash
mcptools bench server.py                                      # All tools, 10 runs
mcptools bench server.py --tool search --params '{"q":"test"}' # Specific tool
mcptools bench server.py --runs 100                           # More runs for accuracy
```

Reports avg, min, max, P50, P95, and error count per tool. Auto-generates minimal valid parameters for tools you don't specify.

### GitHub Action

Gate PRs on MCP server quality:

```yaml
- name: Validate MCP server
  uses: Pavankumardhruv/mcptools@main
  with:
    server: server.py
    min-score: 80
```

## How It Works

```
  mcptools                          Your MCP Server
  ┌──────────┐     JSON-RPC 2.0    ┌──────────────┐
  │          │───── stdin ─────────►│              │
  │  Client  │                      │   Server     │
  │          │◄──── stdout ────────│              │
  └──────────┘                      └──────────────┘
                                          │
                                       stderr → logs
```

mcptools includes a lightweight JSON-RPC client that speaks the MCP protocol directly over stdio. No MCP SDK required — works with any server in any language.

## Architecture

```
mcptools/
├── cli.py            # Typer CLI — 9 commands
├── client.py         # Lightweight MCP client (JSON-RPC over stdio)
├── utils.py          # Shared inspection utilities
├── init_cmd.py       # Project scaffolding (3 templates)
├── inspect_cmd.py    # Server inspection
├── test_cmd.py       # Interactive tool testing
├── validate_cmd.py   # Best-practice validation (8 checks)
├── dev_cmd.py        # Dev server with auto-reload
├── docs_cmd.py       # Markdown documentation generator
├── proxy_cmd.py      # JSON-RPC traffic proxy
├── diff_cmd.py       # Server capability diffing
└── bench_cmd.py      # Tool benchmarking
```

## Works With

Any MCP server, any language, any framework:

- **Python** — [FastMCP](https://gofastmcp.com), [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- **TypeScript** — [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- **Go** — [mcp-go](https://github.com/mark3labs/mcp-go)
- **Rust** — [mcp-rust](https://github.com/Derek-X-Wang/mcp-rust-sdk)

For developers building MCP servers for **Claude Code**, **Cursor**, **Windsurf**, **Cline**, and more.

## Requirements

- Python 3.10+
- That's it. No MCP SDK needed.

## Contributing

PRs welcome. Please open an issue first for larger changes.

## License

MIT License — see [LICENSE](LICENSE) for details.
