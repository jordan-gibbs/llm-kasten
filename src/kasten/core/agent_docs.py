"""Agent documentation integration — inject kasten docs into agent config files.

Supports: CLAUDE.md, AGENTS.md, GEMINI.md, .github/copilot-instructions.md
By default on init, only creates CLAUDE.md. Others created via --agents flags
or if the file already exists in the repo.
"""

from __future__ import annotations

import re
from pathlib import Path

KASTEN_SECTION_MARKER = "<!-- kasten:start -->"
KASTEN_SECTION_END = "<!-- kasten:end -->"

KASTEN_BLURB = """\

{marker}
## Knowledge Base (kasten)

This project uses kasten as a CLI knowledge base. The `knowledge/` directory contains markdown notes. Append `--json` to any command for structured output.

### Search and read

```bash
kasten search "query" --json                # Full-text search
kasten search "query" --tag ml --json       # Filter by tag, status, date, parent
kasten search "query" --include-body --json # Include full note bodies in results
kasten note show <id> --json                     # Read a note
kasten note show <id1> <id2> <id3> --json        # Read multiple notes at once
kasten note list --json                          # List all notes with summaries
```

### Create and update

```bash
kasten note new "Title" --tag t1 --body-file /tmp/content.md --summary "One-liner" --json
kasten note update <id> --status evergreen --add-tag ml --summary "Updated" --json
```

### Knowledge graph and maintenance

```bash
kasten graph backlinks <id> --json    # What links TO this note
kasten graph hubs --json              # Most linked-to notes
kasten graph broken --json            # Broken [[links]]
kasten lint --json                    # Health check
kasten repair --json                  # Full rebuild + fix broken links + promote notes
kasten status --json                  # Vault overview
```

### Note quality requirements

Every note MUST have:
- At least one tag (`--tag`). REUSE existing tags from `kasten tags -j` -- do not invent new ones unless necessary.
- A summary (`--summary`). One sentence, under 120 characters.
- A body with meaningful content (50+ words).
- Use `--body-file` instead of `--body` to avoid shell escaping issues.

Run `kasten lint -j` to check quality, `kasten repair -j` to auto-fix.

### Key conventions

- Notes live in `knowledge/notes/` as markdown with YAML frontmatter
- Link between notes with `[[note-id]]` syntax
- After editing .md files directly, run `kasten sync` to update the index
- Statuses: draft -> review -> evergreen -> stale -> deprecated -> archive
- Run `kasten --help` for the full command list
{end_marker}
"""

# Which files each agent flag creates
AGENT_FILES = {
    "claude": "CLAUDE.md",
    "agents": "AGENTS.md",
    "gemini": "GEMINI.md",
    "copilot": ".github/copilot-instructions.md",
}


def inject_agent_docs(
    vault_root: Path,
    agents: list[str] | None = None,
) -> list[str]:
    """Inject kasten docs into agent config files.

    Args:
        vault_root: The repo root.
        agents: Which agent files to create. Default: ["claude"].
                Options: "claude", "agents", "gemini", "copilot".
                If a file already exists, it's always updated regardless of this list.
    """
    if agents is None:
        agents = ["claude"]

    blurb = KASTEN_BLURB.format(marker=KASTEN_SECTION_MARKER, end_marker=KASTEN_SECTION_END)
    modified = []

    # Determine which files to handle
    files_to_inject: list[tuple[Path, str]] = []

    # CLAUDE.md
    if "claude" in agents or (vault_root / "CLAUDE.md").exists():
        files_to_inject.append((vault_root / "CLAUDE.md", "CLAUDE.md"))

    # AGENTS.md — prefer uppercase, respect existing lowercase
    if "agents" in agents or (vault_root / "AGENTS.md").exists() or (vault_root / "agents.md").exists():
        if (vault_root / "agents.md").exists() and not (vault_root / "AGENTS.md").exists():
            files_to_inject.append((vault_root / "agents.md", "agents.md"))
        else:
            files_to_inject.append((vault_root / "AGENTS.md", "AGENTS.md"))

    # GEMINI.md
    if "gemini" in agents or (vault_root / "GEMINI.md").exists():
        files_to_inject.append((vault_root / "GEMINI.md", "GEMINI.md"))

    # .github/copilot-instructions.md
    copilot_path = vault_root / ".github" / "copilot-instructions.md"
    if "copilot" in agents or copilot_path.exists():
        files_to_inject.append((copilot_path, ".github/copilot-instructions.md"))

    for filepath, filename in files_to_inject:
        result = _inject_into_file(filepath, blurb, filename)
        if result:
            modified.append(result)

    return modified


def _inject_into_file(filepath: Path, blurb: str, filename: str) -> str | None:
    """Inject the kasten blurb into a single file. Returns action taken or None."""
    if filepath.exists():
        content = filepath.read_text(encoding="utf-8-sig")

        if KASTEN_SECTION_MARKER in content:
            pattern = re.compile(
                re.escape(KASTEN_SECTION_MARKER) + r".*?" + re.escape(KASTEN_SECTION_END),
                re.DOTALL,
            )
            new_content = pattern.sub(blurb.strip(), content)
            if new_content != content:
                filepath.write_text(new_content, encoding="utf-8")
                return f"{filename} (updated)"
            return None
        else:
            separator = "\n\n" if not content.endswith("\n") else "\n"
            filepath.write_text(content + separator + blurb.strip() + "\n", encoding="utf-8")
            return f"{filename} (appended)"
    else:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        header = f"# {filepath.stem}\n"
        filepath.write_text(header + blurb.strip() + "\n", encoding="utf-8")
        return f"{filename} (created)"
