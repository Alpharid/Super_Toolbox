# The Co-op Anything MCP server

`tools/mcp/coop_mcp.py` gives any MCP-capable agent the shared knowledge in this repo plus a
few local, read-only analysis tools. It needs Python 3.9+ and PyYAML (`pip install pyyaml`),
and nothing else. It reads your clone, so `git pull` updates it.

| Tool | What it does |
|---|---|
| `search_directory` | Search the directory of co-op projects and gaps by game, engine, status or QA level |
| `detect_engine` | Scan a game install folder and identify the engine from file signatures, with evidence, hooking tools, anti-cheat warnings and co-op projects on the same engine |
| `game_identity` | SHA-256, architecture and PE details of the game exe, to record the exact build |
| `list_docs`, `read_playbook`, `get_skill`, `get_game` | Read the playbook, the agent skills and the game write-ups |
| `validate_entry` | Check a directory entry against the schema before contributing it |

Pair it with a reverse-engineering MCP such as [REA](https://github.com/morluto/rea) for the
binary work: Co-op Anything knows what to do, REA looks inside the game.

## Setup

**Claude Code:** open this repo and the project's `.mcp.json` offers the server automatically.
From anywhere else:
```
claude mcp add coop-anything -- python <path to clone>/tools/mcp/coop_mcp.py
```

**Codex** (`~/.codex/config.toml`):
```toml
[mcp_servers.coop-anything]
command = "python"
args = ["<path to clone>/tools/mcp/coop_mcp.py"]
```

**Gemini CLI** (`.gemini/settings.json`) and **Cursor** (`.cursor/mcp.json`):
```json
{ "mcpServers": { "coop-anything": { "command": "python", "args": ["<path to clone>/tools/mcp/coop_mcp.py"] } } }
```

Use `python3` instead of `python` on Linux and macOS.

## Ask your agent

```
Use coop-anything: detect the engine of my <game> install at <folder>, check what co-op work
exists for it and for its engine, and tell me which path (revive or build from zero) fits.
```
