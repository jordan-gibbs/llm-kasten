"""Web page ingestion — requires kasten[web] extra."""

from __future__ import annotations

from datetime import UTC, datetime

from kasten.core.frontmatter import render_note
from kasten.models.note import NoteMeta, slugify


def ingest_url(
    vault,
    url: str,
    *,
    title: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Fetch a URL and convert to a raw note in the vault."""
    import httpx
    from bs4 import BeautifulSoup

    try:
        import html2text
    except ImportError:
        html2text = None

    # Fetch
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract title
    page_title = title
    if not page_title:
        if soup.title:
            page_title = soup.title.string or "Untitled"
        elif soup.find("h1"):
            page_title = soup.find("h1").get_text(strip=True)
        else:
            page_title = "Web Import"

    # Extract content
    content_elem = soup.find("article") or soup.find("main") or soup.find("body")
    if content_elem:
        for tag in content_elem.find_all(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()
        html_content = str(content_elem)
    else:
        html_content = resp.text

    # Convert to markdown
    if html2text:
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        md_content = h.handle(html_content)
    else:
        md_content = content_elem.get_text(separator="\n\n") if content_elem else resp.text

    file_id = slugify(page_title)

    notes_dir = vault.notes_dir
    notes_dir.mkdir(parents=True, exist_ok=True)
    dest = notes_dir / f"{file_id}.md"
    counter = 2
    while dest.exists():
        dest = notes_dir / f"{file_id}-{counter}.md"
        counter += 1

    meta = NoteMeta(
        title=page_title,
        id=file_id,
        type="raw",
        status="draft",
        source=url,
        tags=tags or [],
        created=datetime.now(UTC),
    )
    dest.write_text(render_note(meta, md_content), encoding="utf-8")

    now_iso = datetime.now(UTC).isoformat()
    vault.db.execute(
        "INSERT INTO ingest_log (source_url, source_type, raw_path, ingested_at, status) "
        "VALUES (?, 'web', ?, ?, 'raw')",
        (url, dest.relative_to(vault.root).as_posix(), now_iso),
    )
    vault.db.commit()

    return {
        "raw_path": dest.relative_to(vault.root).as_posix(),
        "title": page_title,
        "id": file_id,
        "source": url,
    }
