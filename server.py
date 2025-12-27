#!/usr/bin/env python3
"""
MemoryBase MCP Server

MCP server that collects insights from Claude sessions and sends notifications to Telegram.
When Claude completes a significant task (feature, bugfix, plan), it calls log_insight tool.
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
from dotenv import load_dotenv

load_dotenv()

# Config from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INSIGHTS_FILE = os.getenv("INSIGHTS_FILE", "insights.json")

# MCP Server instance
server = Server("memorybase-mcp")


def load_insights() -> list:
    """Load insights from file."""
    path = Path(INSIGHTS_FILE)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_insights(insights: list):
    """Save insights to file."""
    Path(INSIGHTS_FILE).write_text(
        json.dumps(insights, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


async def send_telegram_notification(insight: dict) -> bool:
    """Send notification to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    type_emoji = {
        "feature": "NEW",
        "bugfix": "FIX",
        "plan": "PLAN",
        "idea": "IDEA",
        "decision": "DECISION",
        "learning": "LEARN",
    }

    emoji = type_emoji.get(insight.get("type", ""), "INFO")

    message = f"""[{emoji}] {insight.get('type', 'unknown').upper()}

Project: {insight.get('project', 'unknown')}
Summary: {insight.get('summary', 'No summary')}

{insight.get('description', '')}

---
{insight.get('timestamp', '')}"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )
            return response.status_code == 200
    except Exception:
        return False


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

This sends a notification to the user's Telegram.""",
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
        ),
        Tool(
            name="get_pending_insights",
            description="Get list of pending insights that haven't been processed yet.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of insights to return",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="mark_insight_processed",
            description="Mark an insight as processed (added to memoryBase).",
            inputSchema={
                "type": "object",
                "properties": {
                    "insight_id": {
                        "type": "string",
                        "description": "ID of the insight to mark as processed"
                    }
                },
                "required": ["insight_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    if name == "log_insight":
        # Create insight record
        insight = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "type": arguments.get("type"),
            "project": arguments.get("project"),
            "summary": arguments.get("summary"),
            "description": arguments.get("description", ""),
            "files_changed": arguments.get("files_changed", []),
            "processed": False
        }

        # Save to file
        insights = load_insights()
        insights.append(insight)
        save_insights(insights)

        # Send Telegram notification
        tg_sent = await send_telegram_notification(insight)

        result = f"Insight logged: {insight['summary']}"
        if tg_sent:
            result += "\nTelegram notification sent."
        else:
            result += "\nTelegram notification failed (check config)."

        return [TextContent(type="text", text=result)]

    elif name == "get_pending_insights":
        limit = arguments.get("limit", 10)
        insights = load_insights()
        pending = [i for i in insights if not i.get("processed", False)][:limit]

        if not pending:
            return [TextContent(type="text", text="No pending insights.")]

        result = f"Found {len(pending)} pending insights:\n\n"
        for i in pending:
            result += f"- [{i['id']}] {i['type']}: {i['summary']} ({i['project']})\n"

        return [TextContent(type="text", text=result)]

    elif name == "mark_insight_processed":
        insight_id = arguments.get("insight_id")
        insights = load_insights()

        for i in insights:
            if i["id"] == insight_id:
                i["processed"] = True
                save_insights(insights)
                return [TextContent(type="text", text=f"Insight {insight_id} marked as processed.")]

        return [TextContent(type="text", text=f"Insight {insight_id} not found.")]

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
