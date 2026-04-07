# kasten

A CLI knowledge base manager built on markdown files. Designed to be driven by both humans and LLM coding agents.

kasten turns a directory of `.md` files into a searchable, interlinked knowledge base with full-text search, a link graph, auto-generated indexes, and structured JSON output on every command.

## Install

```bash
pip install kasten
```

Optional extras:

```bash
pip install kasten[web]         # Web page ingestion
pip install kasten[pdf]         # PDF ingestion
pip install kasten[llm]         # OpenAI-compatible LLM features
pip install kasten[anthropic]   # Anthropic Claude
pip install kasten[watch]       # File watcher mode
```

## Quick start

```bash
kasten init .
kasten note new "My First Note" --tag getting-started --body "# Hello"
kasten search "hello" --json
```

## How it works

`kasten init` creates a `.kasten/` directory (config and SQLite index) and a `knowledge/` directory (your notes):

```
your-repo/
  .kasten/             # Hidden: config, database, templates
  knowledge/
    notes/             # Your markdown notes
    index/             # Auto-generated wiki pages
  CLAUDE.md            # Agent docs (auto-created)
```

Markdown files are the source of truth. The SQLite database is a derived cache rebuilt from files at any time with `kasten sync --force`.

### Note format

Every note is a markdown file with YAML frontmatter:

```yaml
---
title: "Auth Architecture"
id: "auth-architecture"
tags: [auth, security, jwt]
status: "evergreen"
summary: "JWT auth with RS256 and refresh token rotation"
parent: "backend/auth"
created: "2026-04-06T00:00:00+00:00"
---

# Auth Architecture

Content here. Link to other notes with [[session-management]] or [[jwt-tokens|JWT]].
```

### Linking

Use `[[note-id]]` to link between notes. kasten tracks backlinks, detects broken links, finds orphan notes, and ranks hub notes by inbound link count.

### Status lifecycle

```
draft --> review --> evergreen --> stale --> deprecated --> archive
```

`kasten repair` auto-promotes notes that meet quality criteria (has summary, tags, sufficient word count, links).

## Commands

### Search and read

```bash
kasten search "query"                        # Full-text search (FTS5 + BM25)
kasten search "query" --tag ml --status evergreen --json
kasten search "query" --include-body --json  # Include full note bodies
kasten note show <id> --json                 # Read a note
kasten note show <id1> <id2> --json          # Read multiple at once
kasten note list --tag x --status y --json   # Filtered listing
```

### Create and update

```bash
kasten note new "Title" --tag t1 --body "content" --summary "one-liner" --json
kasten note new "Title" --body-file /tmp/content.md --json  # Avoid shell escaping
kasten note new "Title" --template concept --json           # Use a template
kasten note update <id> --status evergreen --add-tag ml --summary "revised" --json
kasten note update <id> --deprecate --superseded-by <new-id> --json
```

### Knowledge graph

```bash
kasten graph backlinks <id> --json    # What links to this note
kasten graph hubs --json              # Most linked-to notes
kasten graph broken --json            # Broken [[links]]
kasten graph stub --json              # Create stubs for all broken links
kasten graph orphans --json           # Notes with no connections
```

### Organize

```bash
kasten topic tree --json              # Hierarchical topic structure
kasten batch tag-add ml --parent deep-learning --json
kasten batch set-status review --tag unreviewed --json
kasten batch deprecate --superseded-by new-note --tag old --json
```

### Maintain

```bash
kasten status --json                  # Vault overview
kasten lint --json                    # 11 health check rules
kasten repair --json                  # Full rebuild + fix links + promote + indexes
kasten dedup --json                   # Find near-duplicate notes
kasten sync                           # Rebuild index from files
```

### Advanced

```bash
kasten ingest file ./doc.md --tag ref --json   # Ingest local files
kasten ingest web "https://..." --json         # Ingest web pages
kasten compile --all --json                    # LLM-compile raw notes
kasten ask "question" --json                   # Q&A against the KB
kasten export json --json                      # Full JSON dump
kasten export vault ./out --tag ml --json      # Export filtered subset
kasten import ./other-kb --prefix imported --json
kasten serve --port 8080                       # Web UI
kasten watch                                   # Auto-sync on file changes
kasten git log --json                          # Notes changed in git history
```

## LLM agent integration

Every command supports `--json` for structured output with a consistent envelope:

```json
{
  "ok": true,
  "data": { ... },
  "count": 42,
  "vault": "/path/to/repo",
  "timestamp": "2026-04-06T00:00:00+00:00"
}
```

### Agent config files

`kasten init` auto-injects usage documentation into agent config files so that any AI coding agent working in the repo knows how to use the knowledge base:

| Flag | File created | Read by |
|------|-------------|---------|
| `--agents claude` (default) | `CLAUDE.md` | Claude Code |
| `--agents agents` | `AGENTS.md` | Cursor, Codex, Copilot, Windsurf, Amp, Devin |
| `--agents gemini` | `GEMINI.md` | Gemini CLI |
| `--agents copilot` | `.github/copilot-instructions.md` | GitHub Copilot |

If any of these files already exist in the repo, kasten appends a marked section (idempotent -- safe to run repeatedly). Update with `kasten config agent-docs`.

### Agent workflow

```bash
# Search with full bodies (one call instead of search + read)
kasten search "auth" --include-body --json

# Create a note (use --body-file for long content)
echo "# Content" > /tmp/note.md
kasten note new "Title" --body-file /tmp/note.md --summary "..." --json

# Update metadata without touching body
kasten note update auth-flow --status evergreen --add-tag reviewed --json

# Fix everything
kasten repair --json
```

## Configuration

`.kasten/config.toml`:

```toml
[vault]
name = "My Research"
knowledge_dir = "knowledge"

[search]
boost_evergreen = 1.5
penalize_deprecated = 0.3

[llm]
provider = "anthropic"
model = "claude-sonnet-4-20250514"
```

See `kasten config show` for all settings.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
