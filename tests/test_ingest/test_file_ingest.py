"""Tests for file ingestion."""

from pathlib import Path

from kasten.ingest.file import ingest_local_file


def test_ingest_markdown(tmp_vault, tmp_path: Path):
    src = tmp_path / "article.md"
    src.write_text("# Great Article\n\nSome content about ML.\n", encoding="utf-8")

    result = ingest_local_file(tmp_vault, src, title="ML Article", tags=["ml"])
    assert "notes/" in result["raw_path"]
    assert (tmp_vault.root / result["raw_path"]).exists()

    # Verify frontmatter was added
    content = (tmp_vault.root / result["raw_path"]).read_text(encoding="utf-8")
    assert "---" in content
    assert "ML Article" in content


def test_ingest_text_file(tmp_vault, tmp_path: Path):
    src = tmp_path / "notes.txt"
    src.write_text("Some plain text notes.\n", encoding="utf-8")

    result = ingest_local_file(tmp_vault, src, tags=["text"])
    content = (tmp_vault.root / result["raw_path"]).read_text(encoding="utf-8")
    assert "type: raw" in content
    assert "Some plain text notes" in content


def test_ingest_python_file(tmp_vault, tmp_path: Path):
    src = tmp_path / "example.py"
    src.write_text("def hello():\n    print('hi')\n", encoding="utf-8")

    result = ingest_local_file(tmp_vault, src, tags=["code"])
    content = (tmp_vault.root / result["raw_path"]).read_text(encoding="utf-8")
    assert "```py" in content or "```python" in content


def test_ingest_collision(tmp_vault, tmp_path: Path):
    src = tmp_path / "doc.md"
    src.write_text("# Doc\nContent", encoding="utf-8")

    r1 = ingest_local_file(tmp_vault, src, title="Same Name")
    r2 = ingest_local_file(tmp_vault, src, title="Same Name")
    assert r1["raw_path"] != r2["raw_path"]


def test_ingest_logs_to_db(tmp_vault, tmp_path: Path):
    src = tmp_path / "logged.md"
    src.write_text("# Logged\nContent", encoding="utf-8")

    ingest_local_file(tmp_vault, src)
    rows = tmp_vault.db.execute("SELECT * FROM ingest_log").fetchall()
    assert len(rows) == 1
    assert rows[0]["source_type"] == "file"
    assert rows[0]["status"] == "raw"


def test_ingest_md_with_existing_frontmatter(tmp_vault, tmp_path: Path):
    src = tmp_path / "existing.md"
    src.write_text(
        "---\ntitle: Existing\nid: existing\ntags: [pre]\n---\n\n# Already formatted\n",
        encoding="utf-8",
    )

    result = ingest_local_file(tmp_vault, src)
    content = (tmp_vault.root / result["raw_path"]).read_text(encoding="utf-8")
    # Should preserve existing frontmatter
    assert "Existing" in content
