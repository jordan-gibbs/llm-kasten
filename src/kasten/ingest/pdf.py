"""PDF ingestion — requires kasten[pdf] extra."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from kasten.models.note import slugify


def _parse_page_range(pages_str: str, max_pages: int) -> list[int]:
    """Parse a page range string like '1-5,10' into a list of page numbers."""
    result = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start, end = int(start), int(end)
            result.extend(range(max(0, start - 1), min(max_pages, end)))
        else:
            page = int(part) - 1
            if 0 <= page < max_pages:
                result.append(page)
    return sorted(set(result))


def ingest_pdf_file(
    vault,
    source_path: Path,
    *,
    title: str | None = None,
    tags: list[str] | None = None,
    pages: str | None = None,
) -> dict:
    """Extract text from a PDF and save as a raw note in the vault."""
    import fitz  # PyMuPDF

    source_path = source_path.resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {source_path}")

    doc = fitz.open(str(source_path))

    # Extract title from PDF metadata
    pdf_title = title or doc.metadata.get("title") or source_path.stem.replace("-", " ").title()

    # Determine pages to extract
    page_nums = list(range(len(doc)))
    if pages:
        page_nums = _parse_page_range(pages, len(doc))

    # Extract text
    text_parts = []
    for page_num in page_nums:
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            text_parts.append(f"## Page {page_num + 1}\n\n{text}")

    doc.close()
    md_content = "\n\n".join(text_parts)

    file_id = slugify(pdf_title)
    now_iso = datetime.now(UTC).isoformat()
    tags_yaml = ", ".join(tags) if tags else ""

    notes_dir = vault.notes_dir
    notes_dir.mkdir(parents=True, exist_ok=True)
    dest = notes_dir / f"{file_id}.md"
    counter = 2
    while dest.exists():
        dest = notes_dir / f"{file_id}-{counter}.md"
        counter += 1

    full_content = (
        f"---\n"
        f"title: \"{pdf_title}\"\n"
        f"id: \"{file_id}\"\n"
        f"type: raw\n"
        f"status: draft\n"
        f"source: \"{source_path}\"\n"
        f"tags: [{tags_yaml}]\n"
        f"created: {now_iso}\n"
        f"---\n\n"
        f"{md_content}"
    )

    dest.write_text(full_content, encoding="utf-8")

    vault.db.execute(
        "INSERT INTO ingest_log (source_url, source_type, raw_path, ingested_at, status) "
        "VALUES (?, 'pdf', ?, ?, 'raw')",
        (str(source_path), dest.relative_to(vault.root).as_posix(), now_iso),
    )
    vault.db.commit()

    return {
        "raw_path": dest.relative_to(vault.root).as_posix(),
        "title": pdf_title,
        "id": file_id,
        "source": str(source_path),
        "pages_extracted": len(page_nums),
    }
