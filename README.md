# MemoryBase MCP Server

MCP server that sends insights from Claude sessions to your server.

## How it works

1. You add this MCP server to Claude Code / Claude Desktop
2. When Claude completes significant tasks, it calls `log_insight`
3. MCP sends HTTP request to your server (tg-bot)
4. Server sends Telegram notification with [Да] [Изменить] [Нет] buttons
5. You confirm → insight is analyzed and saved to memoryBase

## Architecture

```
Claude (any session)
    ↓
MCP (log_insight)
    ↓ HTTP POST
Server (tg-bot)
    ↓
Telegram notification
    ↓
User confirms → saves to memoryBase
```

## Tools

| Tool | Description |
|------|-------------|
| `log_insight` | Log an insight (feature, bugfix, plan, idea, decision, learning) |

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
- `SERVER_URL` - URL of your server with tg-bot (e.g., `http://your-server:8585`)
- `API_SECRET` - Secret key (must match tg-bot's API_SECRET)

### 4. Add to Claude Code

Edit `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memorybase": {
      "command": "/path/to/memorybase-mcp/venv/bin/python",
      "args": ["/path/to/memorybase-mcp/server.py"],
      "env": {
        "SERVER_URL": "http://your-server:8585",
        "API_SECRET": "your_secret"
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
        "SERVER_URL": "http://your-server:8585",
        "API_SECRET": "your_secret"
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

## License

MIT
