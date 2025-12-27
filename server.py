#!/usr/bin/env python3
"""
MemoryBase MCP Server

MCP server that sends insights to the server API.
The server then sends Telegram notification with confirmation buttons.
"""

import os
import asyncio
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
from dotenv import load_dotenv

load_dotenv()

# Config from environment
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8585")
API_SECRET = os.getenv("API_SECRET", "")

# MCP Server instance
server = Server("memorybase-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="log_insight",
            description="""Log an insight when you complete something significant.

Call this tool after:
- Completing a large feature
- Fixing a complex bug
- Finishing a multi-step plan (5+ steps)
- Making an important architectural decision
- Learning something valuable

This sends a request to the server which notifies the user via Telegram.
The user can confirm, edit, or reject the insight.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["feature", "bugfix", "plan", "idea", "decision", "learning"],
                        "description": "Type of insight"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name (e.g., timo-rpg, memorybase)"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief one-line summary"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of what was done"
                    },
                    "files_changed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of files that were changed (optional)"
                    }
                },
                "required": ["type", "project", "summary"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    if name == "log_insight":
        # Create insight payload
        payload = {
            "type": arguments.get("type"),
            "project": arguments.get("project"),
            "summary": arguments.get("summary"),
            "description": arguments.get("description", ""),
            "files_changed": arguments.get("files_changed", []),
        }

        # Send to server API
        headers = {}
        if API_SECRET:
            headers["Authorization"] = f"Bearer {API_SECRET}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SERVER_URL}/api/insight",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return [TextContent(
                        type="text",
                        text=f"Insight sent to server. ID: {data.get('id', 'unknown')}\n"
                             f"Telegram notification sent. Waiting for user confirmation."
                    )]
                else:
                    error = response.json().get("error", "Unknown error")
                    return [TextContent(
                        type="text",
                        text=f"Failed to send insight: {error}"
                    )]

        except httpx.ConnectError:
            return [TextContent(
                type="text",
                text=f"Failed to connect to server at {SERVER_URL}. "
                     f"Make sure the server is running."
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error sending insight: {str(e)}"
            )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
