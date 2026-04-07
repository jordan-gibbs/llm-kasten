"""Semantic / vector search using embeddings."""

from __future__ import annotations

import math
import struct
import sqlite3


def cosine_similarity(a: bytes, b: bytes, dims: int) -> float:
    """Compute cosine similarity between two packed float32 vectors."""
    va = struct.unpack(f"{dims}f", a)
    vb = struct.unpack(f"{dims}f", b)
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(x * x for x in vb))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search_semantic(
    conn: sqlite3.Connection,
    query_vector: bytes,
    query_dims: int,
    *,
    limit: int = 20,
) -> list[dict]:
    """Brute-force cosine similarity search against all embeddings."""
    rows = conn.execute(
        "SELECT e.note_id, e.vector, e.dimensions, n.title, n.path, n.status "
        "FROM embeddings e JOIN notes n ON e.note_id = n.id"
    ).fetchall()

    scored = []
    for row in rows:
        sim = cosine_similarity(query_vector, row["vector"], row["dimensions"])
        scored.append({
            "id": row["note_id"],
            "title": row["title"],
            "path": row["path"],
            "status": row["status"],
            "score": sim,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
