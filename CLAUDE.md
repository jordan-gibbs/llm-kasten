# kasten

LLM-powered CLI knowledge base manager. Markdown files with YAML frontmatter as source of truth, SQLite for fast search/indexing.

## Project structure
- `src/kasten/` — main package (src layout)
- `tests/` — pytest test suite (76 tests)
- Entry points: `kasten` and `kas` (alias)

## Commands
```
pip install -e ".[dev]"          # Install in dev mode
python -m pytest tests/ -v       # Run tests
kasten init <path>               # Create vault (--agents claude|agents|gemini|copilot|all)
kasten sync                      # Sync files -> DB
kasten repair                    # Full rebuild + fix links + promote + indexes
kasten search <query>       # Full-text search
kasten note list --json          # JSON output for LLM agents
```

## Architecture
- **File-first**: .md files are truth, SQLite is rebuildable cache
- **Single visible dir**: `knowledge/` at repo root, `.kasten/` hidden
- **Dual output**: Every command supports --json for LLM agent consumption
- **FTS5**: SQLite FTS5 for search, porter stemming + unicode + BM25 ranking
- **Sync**: mtime + SHA-256 change detection, BEGIN IMMEDIATE transactions
- **Links**: [[wiki-links]] parsed, resolved, backlinks computed
- **Agent docs**: Auto-injects into CLAUDE.md, AGENTS.md, GEMINI.md, copilot-instructions.md

## Key conventions
- All frontmatter uses `yaml.safe_load` / Pydantic v2 for validation
- Enums serialize via `model_dump(mode="json")`
- UTF-8-sig encoding for reading (handles BOM)
- Slug IDs preserve underscores (used by index pages)
- Vault path properties: `vault.notes_dir`, `vault.index_dir`, `vault.knowledge_dir`
- Per-tag index pages only generated for tags with 3+ notes
