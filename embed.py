"""
Milestone 4a — Embedding and vector store
The Unofficial Guide: Student Technology Survival Guide

What this script does (matches planning.md > Retrieval Approach):
  1. LOAD    the chunks produced by ingest.py (chunks.json)
  2. EMBED   each chunk with all-MiniLM-L6-v2 (sentence-transformers)
  3. STORE   the vectors + text + source metadata in a persistent ChromaDB
             collection on disk (chroma_db/)

Run:  python embed.py        # (re)builds the index from scratch

The shared helpers here (get_model, get_collection) are imported by retrieve.py
so embedding and querying always use the exact same model and collection.
"""

from __future__ import annotations

import os

# Silence the "tokenizers ... process just got forked" warning that appears when
# the embedding model is used and then the Groq HTTP client forks. Must be set
# before sentence-transformers/tokenizers is imported, so it lives at the top.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import json
from functools import lru_cache
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
MODEL_NAME = "all-MiniLM-L6-v2"      # from planning.md > Retrieval Approach
CHUNKS_FILE = Path("chunks.json")    # output of ingest.py
CHROMA_DIR = Path("chroma_db")       # on-disk vector store (gitignored)
COLLECTION_NAME = "unofficial_guide"

# Metadata fields copied from each chunk onto its vector. ChromaDB metadata
# must be str/int/float/bool — all of these qualify.
METADATA_FIELDS = ("source_file", "source_type", "chunk_index", "word_count")


# --------------------------------------------------------------------------- #
# Shared helpers (also used by retrieve.py)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def get_model():
    """Load the embedding model once and reuse it (it takes a few seconds)."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def get_client():
    """Persistent ChromaDB client — survives between runs (stored on disk)."""
    import chromadb
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection():
    """
    Return the collection, creating it if needed.

    We pin the distance metric to cosine ("hnsw:space": "cosine") because
    sentence-transformers embeddings are compared by direction, not magnitude.
    Chroma's default is squared-L2, which would give worse rankings here.
    """
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Encode a list of strings into embedding vectors (as plain lists)."""
    model = get_model()
    vectors = model.encode(texts, batch_size=32, show_progress_bar=True)
    return vectors.tolist()


# --------------------------------------------------------------------------- #
# Index builder
# --------------------------------------------------------------------------- #
def load_chunks() -> list[dict]:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"'{CHUNKS_FILE}' not found. Run `python ingest.py` first."
        )
    return json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))


def build_index() -> int:
    """Rebuild the collection from chunks.json. Returns number of chunks indexed."""
    chunks = load_chunks()
    if not chunks:
        raise ValueError("chunks.json is empty — nothing to index.")

    # Start clean so re-running doesn't create duplicate vectors.
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # collection didn't exist yet — fine on first run
    collection = get_collection()

    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [{k: c[k] for k in METADATA_FIELDS} for c in chunks]

    print(f"Embedding {len(documents)} chunks with '{MODEL_NAME}'...")
    embeddings = embed_texts(documents)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(
        f"\nDone. Indexed {collection.count()} chunks into "
        f"'{COLLECTION_NAME}' at {CHROMA_DIR}/"
    )
    return collection.count()


if __name__ == "__main__":
    build_index()
