# LLM-Kasten: Agentic Knowledge Management

![LLM-Kasten](assets/hero-graph.svg)

[![PyPI](https://img.shields.io/pypi/v/llm-kasten)](https://pypi.org/project/llm-kasten/)
[![CI](https://github.com/jordan-gibbs/llm-kasten/actions/workflows/ci.yml/badge.svg)](https://github.com/jordan-gibbs/llm-kasten/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://pypi.org/project/llm-kasten/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A CLI [Zettelkasten](https://en.wikipedia.org/wiki/Zettelkasten) for LLM coding agents. Markdown notes with `[[wiki-links]]`, full-text search, a knowledge graph, and structured JSON output on every command.

Inspired by [Andrej Karpathy's approach](https://x.com/karpathy/status/2039805659525644595) to building LLM-maintained personal knowledge bases from markdown.

```bash
pip install llm-kasten
kasten init .
kasten search "auth" -j   # structured JSON with full note bodies
```

<!-- TODO: Add terminal recording GIF here -->

## How it works

`kasten init` adds a `knowledge/` directory and a `.kasten/` engine to your repo. It auto-injects usage docs into CLAUDE.md so agents discover the tool immediately.

```
your-repo/
  .kasten/             # Hidden: config, SQLite index
  knowledge/
    notes/             # Markdown notes (source of truth)
    index/             # Auto-generated wiki pages
  CLAUDE.md            # Agent docs (auto-injected)
```

Notes are plain markdown with YAML frontmatter. Kasten indexes them with SQLite FTS5, computes `[[wiki-link]]` backlinks, and rebuilds the index from files at any time (`kasten sync --force`). Files outlast tools.

## Essential commands

```bash
kasten search "query" -j              # Full-text search, returns bodies
kasten note show <id> -j              # Read a note (or pass multiple IDs)
kasten note new "Title" --tag t \
  --body-file content.md \
  --summary "one-liner" -j            # Create with content from file
kasten note update <id> \
  --status evergreen --add-tag ml -j  # Update metadata
kasten repair -j                      # Fix links, promote notes, rebuild indexes
```

Every command returns `{"ok": true, "data": {...}}`. Append `-j` for JSON.

[Full command reference](https://github.com/jordan-gibbs/llm-kasten/blob/main/CHANGELOG.md)

## Agent integration

Kasten auto-injects a usage guide into agent config files at `kasten init`:

| Flag | File | Agents |
|------|------|--------|
| `--agents claude` (default) | `CLAUDE.md` | Claude Code |
| `--agents agents` | `AGENTS.md` | Cursor, Codex, Copilot, Windsurf, Amp, Devin |
| `--agents gemini` | `GEMINI.md` | Gemini CLI |
| `--agents copilot` | `.github/copilot-instructions.md` | GitHub Copilot |

For agents that use MCP (Claude Desktop, Cursor inline):

```bash
pip install llm-kasten[mcp]
```

```json
{"mcpServers": {"kasten": {"command": "kasten", "args": ["mcp"]}}}
```

8 read-only tools: `search_notes`, `read_note`, `read_many`, `list_notes`, `get_backlinks`, `get_hubs`, `vault_status`, `lint_vault`.

## Knowledge graph

Notes link to each other with `[[wiki-links]]`. Kasten tracks backlinks, finds broken links, detects orphan notes, and ranks hub notes by inbound link count. `kasten serve` renders an interactive force-directed graph in the browser.

## Note lifecycle

```
draft --> review --> evergreen --> stale --> deprecated --> archive
```

`kasten repair` auto-promotes notes that have a summary, tags, and 50+ words (draft to review), plus links and 100+ words (review to evergreen). It also auto-fills missing tags and summaries from note content.

## Requirements

- Python 3.11+
- Works on Windows, macOS, Linux
- SQLite with FTS5 (included in Python's bundled SQLite)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
