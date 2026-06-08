"""
Milestone 4b — Retrieval
The Unofficial Guide: Student Technology Survival Guide

Embeds a user's question with the same model used at index time, then asks
ChromaDB for the top-k most similar chunks (planning.md > Retrieval Approach:
top-k = 5). Returns the chunk text plus its source metadata so the answer can
be attributed back to a document.

Use as a library (Milestone 5 generation will call search()):
    from retrieve import search
    hits = search("How do I reset my password?")

Or test from the command line:
    python retrieve.py "How do I connect to campus Wi-Fi?"
    python retrieve.py                # interactive prompt
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from embed import get_collection, get_model

TOP_K = 5   # planning.md > Retrieval Approach


@dataclass
class Hit:
    rank: int
    text: str
    source_file: str
    source_type: str
    chunk_index: int
    similarity: float   # 1.0 = identical direction, 0.0 = unrelated


def search(query: str, top_k: int = TOP_K) -> list[Hit]:
    """Return the top_k most similar chunks to `query`, best first."""
    if not query.strip():
        return []

    query_embedding = get_model().encode([query]).tolist()
    results = get_collection().query(
        query_embeddings=query_embedding,
        n_results=top_k,
    )

    # Chroma returns parallel lists wrapped one level deep (one entry per query).
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    hits: list[Hit] = []
    for rank, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), start=1):
        hits.append(
            Hit(
                rank=rank,
                text=doc,
                source_file=meta.get("source_file", "?"),
                source_type=meta.get("source_type", "?"),
                chunk_index=meta.get("chunk_index", -1),
                similarity=round(1.0 - dist, 4),  # cosine distance -> similarity
            )
        )
    return hits


def _print_hits(query: str, hits: list[Hit]) -> None:
    print(f'\nQuery: "{query}"  (top {len(hits)})\n' + "-" * 60)
    if not hits:
        print("No results. Did you run `python embed.py` first?")
        return
    for h in hits:
        preview = h.text[:200] + ("..." if len(h.text) > 200 else "")
        print(
            f"#{h.rank}  sim={h.similarity:<6}  "
            f"{h.source_file} [chunk {h.chunk_index}]\n    {preview}\n"
        )


def main() -> int:
    if len(sys.argv) > 1:
        queries = [" ".join(sys.argv[1:])]
    else:
        try:
            queries = [input("Ask a question: ")]
        except (EOFError, KeyboardInterrupt):
            return 0

    for q in queries:
        _print_hits(q, search(q))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
