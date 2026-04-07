"""Local file ingestion."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from kasten.core.frontmatter import render_note
from kasten.models.note import NoteMeta, slugify


def _make_meta(
    file_title: str,
    file_id: str,
    source: str,
    tags: list[str] | None,
) -> NoteMeta:
    """Build a raw note's frontmatter metadata."""
    return NoteMeta(
        title=file_title,
        id=file_id,
        type="raw",
        status="draft",
        source=source,
        tags=tags or [],
        created=datetime.now(timezone.utc),
    )


def _unique_dest(base_dir: Path, file_id: str) -> Path:
    """Find a non-colliding destination path."""
    dest = base_dir / f"{file_id}.md"
    counter = 2
    while dest.exists():
        dest = base_dir / f"{file_id}-{counter}.md"
        counter += 1
    return dest


def ingest_local_file(
    vault,
    source_path: Path,
    *,
    title: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Ingest a local file into the vault as a raw note."""
    source_path = source_path.resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {source_path}")

    file_title = title or source_path.stem.replace("-", " ").replace("_", " ").title()
    file_id = slugify(file_title)

    notes_dir = vault.notes_dir
    notes_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(notes_dir, file_id)

    suffix = source_path.suffix.lower()
    source_str = source_path.as_posix()  # Forward slashes for YAML safety
    meta = _make_meta(file_title, file_id, source_str, tags)

    if suffix == ".md":
        content = source_path.read_text(encoding="utf-8")
        if content.startswith("---"):
            # Already has frontmatter, copy as-is
            dest.write_text(content, encoding="utf-8")
        else:
            dest.write_text(render_note(meta, content), encoding="utf-8")
    elif suffix in (".txt", ".rst", ".org"):
        content = source_path.read_text(encoding="utf-8")
        dest.write_text(render_note(meta, content), encoding="utf-8")
    elif suffix in (".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".sh", ".rb"):
        content = source_path.read_text(encoding="utf-8")
        lang = suffix.lstrip(".")
        body = f"```{lang}\n{content}\n```\n"
        dest.write_text(render_note(meta, body), encoding="utf-8")
    else:
        # Binary or unknown — copy file and create reference note
        bin_dest = notes_dir / source_path.name
        shutil.copy2(source_path, bin_dest)
        body = f"Binary file: [{source_path.name}]({source_path.name})\n"
        dest.write_text(render_note(meta, body), encoding="utf-8")

    # Log ingestion
    now_iso = datetime.now(timezone.utc).isoformat()
    vault.db.execute(
        "INSERT INTO ingest_log (source_url, source_type, raw_path, ingested_at, status) "
        "VALUES (?, 'file', ?, ?, 'raw')",
        (source_str, dest.relative_to(vault.root).as_posix(), now_iso),
    )
    vault.db.commit()

    return {
        "raw_path": dest.relative_to(vault.root).as_posix(),
        "title": file_title,
        "id": file_id,
        "source": source_str,
    }
