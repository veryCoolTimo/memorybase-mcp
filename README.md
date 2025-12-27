# MemoryBase MCP Server

MCP server that collects insights from Claude sessions and sends notifications to Telegram.

## How it works

1. You add this MCP server to Claude Code / Claude Desktop
2. When Claude completes significant tasks, it automatically calls `log_insight`
3. You receive a Telegram notification
4. Insights are saved and can be processed later

## Tools

| Tool | Description |
|------|-------------|
| `log_insight` | Log an insight (feature, bugfix, plan, idea, decision, learning) |
| `get_pending_insights` | Get list of unprocessed insights |
| `mark_insight_processed` | Mark insight as processed |

## Triggers

Claude should call `log_insight` after:
- Completing a large feature
- Fixing a complex bug
- Finishing a multi-step plan (5+ steps)
- Making an important architectural decision
- Learning something valuable

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:veryCoolTimo/memorybase-mcp.git
cd memorybase-mcp
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
nano .env
```

Fill in:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `TELEGRAM_CHAT_ID` - Your Telegram user ID

### 4. Add to Claude Code

Edit `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memorybase": {
      "command": "/path/to/memorybase-mcp/venv/bin/python",
      "args": ["/path/to/memorybase-mcp/server.py"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_token",
        "TELEGRAM_CHAT_ID": "your_id"
      }
    }
  }
}
```

Or for Claude Code CLI, add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "memorybase": {
      "command": "python",
      "args": ["./tools/memorybase-mcp/server.py"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_token",
        "TELEGRAM_CHAT_ID": "your_id"
      }
    }
  }
}
```

## Usage

Once configured, Claude will automatically log insights. You can also explicitly ask:

```
"Log this as a feature insight for project X"
```

## Telegram Notification Format

```
[FEATURE] feature

Project: timo-rpg
Summary: Added DM mode with real-time sync

Implemented virtual tabletop with fog of war...

---
2025-12-27T22:00:00
```

## License

MIT
