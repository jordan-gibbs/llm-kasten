"""Topic cluster computation from tag co-occurrence and link structure."""

from __future__ import annotations

import sqlite3
from collections import defaultdict


def compute_clusters(conn: sqlite3.Connection, min_shared_tags: int = 2) -> list[dict]:
    """Compute topic clusters from notes that share multiple tags.

    Groups notes by tag co-occurrence patterns. Returns clusters sorted by size.
    Each cluster: {"label": str, "tags": list[str], "notes": list[str], "count": int}
    """
    # Get all note-tag pairs (excluding index/raw)
    rows = conn.execute(
        "SELECT t.note_id, t.tag FROM tags t "
        "JOIN notes n ON t.note_id = n.id "
        "WHERE n.type NOT IN ('index', 'raw')"
    ).fetchall()

    # Build note -> tags mapping
    note_tags: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        note_tags[r["note_id"]].add(r["tag"])

    # Find tag co-occurrence: which tags frequently appear together
    tag_pairs: dict[tuple[str, str], int] = defaultdict(int)
    for tags in note_tags.values():
        tag_list = sorted(tags)
        for i in range(len(tag_list)):
            for j in range(i + 1, len(tag_list)):
                tag_pairs[(tag_list[i], tag_list[j])] += 1

    # Build clusters via connected components of frequently co-occurring tags
    # Start with the most common tag pairs
    strong_pairs = [(pair, count) for pair, count in tag_pairs.items() if count >= min_shared_tags]
    strong_pairs.sort(key=lambda x: x[1], reverse=True)

    # Union-Find for clustering tags
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        if x not in parent:
            parent[x] = x
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for (tag_a, tag_b), _ in strong_pairs:
        union(tag_a, tag_b)

    # Group tags by cluster root
    tag_clusters: dict[str, set[str]] = defaultdict(set)
    for tag in parent:
        root = find(tag)
        tag_clusters[root].add(tag)

    # For each cluster, find which notes belong (have 2+ of the cluster's tags)
    clusters = []
    for root, cluster_tags in tag_clusters.items():
        if len(cluster_tags) < 2:
            continue
        cluster_notes = []
        for note_id, tags in note_tags.items():
            overlap = tags & cluster_tags
            if len(overlap) >= min_shared_tags:
                cluster_notes.append(note_id)

        if len(cluster_notes) < 2:
            continue

        # Label: most popular tag in the cluster
        tag_counts = conn.execute(
            f"SELECT tag, COUNT(*) as c FROM tags WHERE tag IN ({','.join('?' for _ in cluster_tags)}) "
            f"GROUP BY tag ORDER BY c DESC LIMIT 1",
            list(cluster_tags),
        ).fetchone()
        label = tag_counts["tag"] if tag_counts else root

        clusters.append({
            "label": label,
            "tags": sorted(cluster_tags),
            "notes": sorted(cluster_notes),
            "count": len(cluster_notes),
        })

    clusters.sort(key=lambda c: c["count"], reverse=True)
    return clusters
