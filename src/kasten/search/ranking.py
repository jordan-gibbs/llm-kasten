"""Result scoring and merging for hybrid search."""

from __future__ import annotations


def merge_results(
    fts_results: list[dict],
    semantic_results: list[dict],
    *,
    fts_weight: float = 0.6,
    semantic_weight: float = 0.4,
) -> list[dict]:
    """Merge FTS and semantic results using weighted scoring."""
    scores: dict[str, dict] = {}

    # Normalize FTS scores
    if fts_results:
        max_fts = max(r["score"] for r in fts_results) or 1
        for _rank, r in enumerate(fts_results):
            nid = r["id"]
            scores[nid] = {
                **r,
                "fts_score": r["score"] / max_fts,
                "semantic_score": 0.0,
            }

    # Normalize semantic scores
    if semantic_results:
        for r in semantic_results:
            nid = r["id"]
            if nid in scores:
                scores[nid]["semantic_score"] = r["score"]
            else:
                scores[nid] = {
                    **r,
                    "fts_score": 0.0,
                    "semantic_score": r["score"],
                }

    # Compute combined score
    for _nid, entry in scores.items():
        entry["score"] = (
            entry["fts_score"] * fts_weight + entry["semantic_score"] * semantic_weight
        )

    return sorted(scores.values(), key=lambda x: x["score"], reverse=True)
