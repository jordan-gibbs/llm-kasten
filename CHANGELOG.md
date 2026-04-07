# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-06

Initial release.

### Core

- Markdown files with YAML frontmatter as the source of truth
- SQLite FTS5 full-text search with BM25 ranking and porter stemming
- `[[wiki-link]]` parsing with backlink tracking and broken link detection
- mtime + SHA-256 change detection with atomic transactions
- Configurable search ranking (boost evergreen, penalize deprecated)

### CLI commands

- `kasten init` -- initialize a vault with `--agents` flag for agent config files
- `kasten search` -- full-text search with tag, status, date, parent, word count filters
- `kasten note new` -- create notes with `--body`, `--body-file`, `--template`, `--summary`
- `kasten note show` -- read one or multiple notes at once
- `kasten note list` -- list and filter notes
- `kasten note update` -- update frontmatter fields on a single note
- `kasten note edit` / `mv` / `rm` -- file operations
- `kasten graph backlinks` / `outlinks` / `orphans` / `broken` / `hubs` / `stub`
- `kasten lint` -- health checks with 11 rules including expired, deprecated, stale reviews
- `kasten repair` -- full rebuild, stub broken links, promote notes, rebuild indexes
- `kasten batch` -- bulk tag, status, parent, deprecate operations with `--dry-run`
- `kasten topic tree` / `list` / `show` -- hierarchical parent navigation
- `kasten ingest file` / `web` / `pdf` -- source material ingestion
- `kasten compile` -- LLM compilation of raw notes (OpenAI, Anthropic, Ollama)
- `kasten ask` -- Q&A against the knowledge base
- `kasten index build` -- auto-generated wiki index pages
- `kasten export json` / `vault` -- JSON dump and filtered vault export
- `kasten import` -- import notes from another directory
- `kasten dedup` -- find near-duplicate notes by content similarity
- `kasten template list` / `show` -- built-in note templates
- `kasten git log` / `blame` / `changed` -- git integration
- `kasten watch` -- file watcher with auto-sync
- `kasten serve` -- lightweight web UI for browsing

### Agent integration

- `--json` flag on every command with consistent envelope format
- Auto-injects usage docs into CLAUDE.md, AGENTS.md, GEMINI.md, copilot-instructions.md
- `--body-file` flag to avoid shell escaping issues
- Duplicate detection on note creation
- `--include-body` on search to combine search + read in one call

### Note lifecycle

- Status progression: draft, review, evergreen, stale, deprecated, archive
- `superseded_by`, `deprecated`, `confidence`, `reviewed`, `expires` frontmatter fields
- Auto-promotion via `kasten promote` / `kasten repair`
- Lint rules for expired notes, deprecated without successor, stale reviews, low confidence

[0.1.0]: https://github.com/jordan-gibbs/kasten/releases/tag/v0.1.0
