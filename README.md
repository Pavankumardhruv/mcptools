<p align="center">
  <h1 align="center">mcptools</h1>
</p>

<p align="center">
  <strong>The Swiss Army knife for MCP server development.</strong><br>
  Scaffold. Inspect. Test. Validate. Ship.
</p>

<p align="center">
  <a href="https://github.com/Pavankumardhruv/mcptools/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Pavankumardhruv/mcptools?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/protocol-MCP-purple?style=flat-square" alt="MCP">
</p>

---

Building MCP servers is easy. Building them **well** is harder. mcptools gives you a complete development toolkit — from scaffolding to validation — so you can ship MCP servers with confidence.

**Zero dependencies on the MCP SDK.** mcptools connects to any MCP server over stdio using the JSON-RPC protocol directly. Works with Python, Node.js, Go — anything that speaks MCP.

## Demo

```bash
$ mcptools init my-weather-server

  Created my-weather-server/

    server.py              MCP server with example tools
    pyproject.toml         Project config
    tests/test_server.py   Tests using FastMCP Client
    README.md              Documentation

  Next steps:

    cd my-weather-server
    pip install -e .
    mcptools inspect server.py
    mcptools test server.py
```

```bash
$ mcptools inspect server.py

╭──────────── Server Capabilities ────────────╮
│ my-weather-server v0.1.0                    │
│                                             │
│ 2 tools  ·  1 resources  ·  1 prompts      │
╰─────────────────────────────────────────────╯

┌──────────────── Tools ─────────────────┐
│ Name     │ Description        │ Params │
├──────────┼────────────────────┼────────┤
│ greet    │ Greet someone by   │ name:  │
│          │ name               │ string │
├──────────┼────────────────────┼────────┤
│ add      │ Add two numbers    │ a: int │
│          │ together           │ b: int │
└──────────┴────────────────────┴────────┘
```

```bash
$ mcptools test server.py --tool greet --params '{"name": "World"}'

╭──── Result: greet ────╮
│ Hello, World!         │
╰───────────────────────╯
```

```bash
$ mcptools validate server.py

┌──────────── Validation Results ────────────┐
│ Check              │ Status │ Details       │
├────────────────────┼────────┼───────────────┤
│ Tool Naming        │  PASS  │ ✓ ✓           │
│ Tool Descriptions  │  PASS  │ ✓ ✓           │
│ Parameter Schemas  │  WARN  │ ⚠ no desc     │
│ Uniqueness         │  PASS  │ ✓ ✓ ✓         │
│ Tool Count         │  PASS  │ ✓ 2 tools     │
│ Prompt Descriptions│  PASS  │ ✓             │
└────────────────────┴────────┴───────────────┘

╭──── Score ────╮
│  85/100       │
╰───────────────╯
```

## Install

```bash
pip install git+https://github.com/Pavankumardhruv/mcptools.git
```

Or clone and install locally:

```bash
git clone https://github.com/Pavankumardhruv/mcptools.git
cd mcptools
pip install -e .
```

## Commands

### `mcptools init <name>`

Scaffold a new MCP server project with [FastMCP](https://gofastmcp.com).

```bash
mcptools init my-server
cd my-server
pip install -e .
```

Creates a complete project with:
- `server.py` — MCP server with example tools, resources, and prompts
- `pyproject.toml` — Dependencies and project config
- `tests/` — Test setup using FastMCP's in-memory client
- Git repo initialized

### `mcptools inspect <server>`

Connect to any MCP server and display its capabilities in rich terminal tables.

```bash
mcptools inspect server.py              # Python server
mcptools inspect server.js              # Node.js server
mcptools inspect "python server.py"     # Explicit command
mcptools inspect server.py --json       # Raw JSON output
```

Shows:
- Server name and version
- All tools with descriptions and parameter schemas
- All resources with URIs and MIME types
- All prompts with arguments

### `mcptools test <server>`

Interactively test tools on a running MCP server.

```bash
# Interactive mode — pick tools, enter params, see results
mcptools test server.py

# Non-interactive — great for CI/scripts
mcptools test server.py --tool greet --params '{"name": "World"}'
```

### `mcptools validate <server>`

Lint your MCP server against best practices from the [MCP specification](https://modelcontextprotocol.io).

```bash
mcptools validate server.py
```

**Checks:**

| Check | What it validates |
|---|---|
| Tool Naming | snake_case, starts with a verb (get_, create_, list_, ...) |
| Tool Descriptions | Present, 10–500 characters, clear and useful |
| Parameter Schemas | Type annotations and descriptions on all params |
| Uniqueness | No duplicate tool names or resource URIs |
| Tool Count | Warns at 20+, fails at 30+ (context bloat) |
| Prompt Descriptions | All prompts have descriptions |

Returns a score out of 100 so you can gate CI on quality:

```bash
mcptools validate server.py --min-score 80   # Exit code 1 if below 80
```

### `mcptools dev <server>`

Run your MCP server in development mode with live reload. Watches for file changes, reconnects, and shows updated capabilities instantly.

```bash
mcptools dev server.py
```

```
mcptools dev · watching /path/to/project · Ctrl+C to stop

╭──────────────────────────────────╮
│ my-server                        │
│                                  │
│ 2 tools  ·  1 resources  ·  1   │
│ prompts                          │
╰──────────────────────────────────╯

 Tool           Description              Params
 greet          Greet someone by name.   name
 add            Add two numbers toget…   a, b

Watching for changes...

Changed: server.py
Reloading...

  Tools: +multiply
```

### `mcptools docs <server>`

Auto-generate Markdown documentation from a live MCP server. Outputs to stdout (pipe to a file) or write directly with `--output`.

```bash
mcptools docs server.py                  # Print to stdout
mcptools docs server.py -o TOOLS.md      # Write to file
```

Generates a clean doc with tool tables, parameter schemas, resource URIs, and prompt arguments — ready to paste into your README.

### GitHub Action

Gate your PRs on MCP server quality. Add to your workflow:

```yaml
- name: Validate MCP server
  uses: Pavankumardhruv/mcptools@main
  with:
    server: server.py
    min-score: 80
```

Installs mcptools, installs your server's dependencies, and fails the step if the validation score is below your threshold.

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

mcptools includes a lightweight JSON-RPC client that speaks the MCP protocol directly over stdio. No MCP SDK required — it works with any server in any language.

**Protocol flow:**
1. Launch server process
2. Send `initialize` with client capabilities
3. Receive server capabilities
4. Send `notifications/initialized`
5. Query tools/resources/prompts or call tools
6. Close connection

## Architecture

```
mcptools/
├── cli.py            # Typer CLI — all commands
├── client.py         # Lightweight MCP client (JSON-RPC over stdio)
├── init_cmd.py       # Project scaffolding
├── inspect_cmd.py    # Server inspection
├── test_cmd.py       # Interactive tool testing
├── validate_cmd.py   # Best-practice validation
├── dev_cmd.py        # Dev server with auto-reload
└── docs_cmd.py       # Markdown documentation generator
```

## Works With

mcptools works with any MCP server, regardless of language or framework:

- **Python** — [FastMCP](https://gofastmcp.com), [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- **TypeScript** — [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- **Go** — [mcp-go](https://github.com/mark3labs/mcp-go)
- **Rust** — [mcp-rust](https://github.com/Derek-X-Wang/mcp-rust-sdk)

Used by developers building MCP servers for **Claude Code**, **Cursor**, **Windsurf**, **Cline**, and other AI tools.

## Requirements

- Python 3.10+
- That's it. No MCP SDK needed.

## Contributing

PRs welcome. Please open an issue first for larger changes.

## License

MIT License — see [LICENSE](LICENSE) for details.
