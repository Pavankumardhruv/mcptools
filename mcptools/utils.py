"""Shared utilities across mcptools commands."""

from .client import MCPClient, parse_server_spec


async def fetch_capabilities(client: MCPClient) -> dict:
    """Fetch all server capabilities in a single call."""
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
        "server_info": client.server_info or {},
        "tools": tools or [],
        "resources": resources or [],
        "prompts": prompts or [],
    }
