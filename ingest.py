"""
Milestone 3 — Document ingestion and chunking
The Unofficial Guide: Student Technology Survival Guide

What this script does (matches planning.md):
  1. LOAD   every file in documents/ (.txt, .md, .html, .pdf)
  2. CLEAN  the extracted text (strip HTML chrome, normalize whitespace)
  3. CHUNK  each document into fixed 180-word windows with 30-word overlap
  4. SAVE   the chunks + source metadata to chunks.json for Milestone 4 (embedding)

Run:  python ingest.py
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration  (these are the numbers from planning.md > Chunking Strategy)
# --------------------------------------------------------------------------- #
CHUNK_SIZE = 180          # words per chunk
OVERLAP = 30              # words shared between consecutive chunks (~17%)

DOCUMENTS_DIR = Path("documents")   # where you drop your source files
OUTPUT_FILE = Path("chunks.json")   # what Milestone 4 will read back in

SUPPORTED_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".pdf"}


# --------------------------------------------------------------------------- #
# Data model — one record per chunk. The metadata fields exist because
# planning.md > Anticipated Challenges calls out source attribution as a
# requirement: every chunk must remember which file it came from.
# --------------------------------------------------------------------------- #
@dataclass
class Chunk:
    chunk_id: str        # e.g. "wifi-setup-0003"
    text: str            # the cleaned chunk text
    source_file: str     # filename it came from, e.g. "wifi-setup.html"
    source_type: str     # file extension without the dot, e.g. "html"
    chunk_index: int     # 0-based position of this chunk within its document
    word_count: int      # number of words in this chunk


# --------------------------------------------------------------------------- #
# 1. LOADERS — one reader per file type. Each returns raw (uncleaned) text.
# --------------------------------------------------------------------------- #
def read_text_file(path: Path) -> str:
    """Plain .txt / .md — read straight off disk as UTF-8."""
    return path.read_text(encoding="utf-8", errors="ignore")


def read_html_file(path: Path) -> str:
    """
    .html / .htm — pull out the human-readable text with BeautifulSoup and
    throw away page chrome (nav bars, scripts, styles, footers) that would
    otherwise pollute the chunks with menu links and cookie banners.
    """
    from bs4 import BeautifulSoup  # imported lazily so the script still runs
                                   # for txt/pdf-only users who skipped bs4

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")

    # Remove elements that are never useful answer content.
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # separator=" " keeps words from running together across tags.
    return soup.get_text(separator=" ")


def read_pdf_file(path: Path) -> str:
    """.pdf — extract text page-by-page with pdfplumber, joined by blank lines."""
    import pdfplumber  # lazy import, same reason as bs4 above

    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def load_raw_text(path: Path) -> str:
    """Dispatch to the right reader based on file extension."""
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return read_text_file(path)
    if ext in {".html", ".htm"}:
        return read_html_file(path)
    if ext == ".pdf":
        return read_pdf_file(path)
    raise ValueError(f"Unsupported file type: {path.name}")


# --------------------------------------------------------------------------- #
# 2. CLEANING — normalize whatever the loaders produced into tidy prose.
# --------------------------------------------------------------------------- #
def clean_text(text: str) -> str:
    """
    Cleaning steps (intentionally conservative — we don't want to delete real
    content, just formatting noise):
      - normalize Windows/Mac line endings to "\n"
      - collapse runs of spaces/tabs into a single space
      - collapse 3+ blank lines down to a single blank line
      - strip leading/trailing whitespace on each line and overall
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)              # collapse horizontal whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)            # collapse big vertical gaps
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


# --------------------------------------------------------------------------- #
# 3. CHUNKING — the core chunk_text() the planning doc asked for.
# --------------------------------------------------------------------------- #
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Split text into fixed-size word windows with overlap (a "sliding window").

    Example with chunk_size=180, overlap=30:
        chunk 0 -> words   0..180
        chunk 1 -> words 150..330   (starts 30 words back into chunk 0)
        chunk 2 -> words 300..480
        ...
    The window advances by (chunk_size - overlap) = 150 words each step, so 30
    words are repeated at every boundary. That repetition is what keeps a fact
    that straddles a split retrievable from at least one chunk.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()           # whitespace tokenization == "words"
    if not words:
        return []

    step = chunk_size - overlap
    chunks: list[str] = []
    for start in range(0, len(words), step):
        window = words[start:start + chunk_size]
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break                  # last window reached the end; stop
    return chunks


# --------------------------------------------------------------------------- #
# 4. PIPELINE — tie loaders + cleaner + chunker together with metadata.
# --------------------------------------------------------------------------- #
def build_chunks_for_file(path: Path) -> list[Chunk]:
    """Load -> clean -> chunk a single file into Chunk records."""
    raw = load_raw_text(path)
    cleaned = clean_text(raw)
    pieces = chunk_text(cleaned)

    stem = path.stem  # filename without extension, used as the id prefix
    source_type = path.suffix.lower().lstrip(".")
    return [
        Chunk(
            chunk_id=f"{stem}-{i:04d}",
            text=piece,
            source_file=path.name,
            source_type=source_type,
            chunk_index=i,
            word_count=len(piece.split()),
        )
        for i, piece in enumerate(pieces)
    ]


def discover_files(documents_dir: Path) -> list[Path]:
    """Return the supported source files in documents/ (sorted, recursive)."""
    return sorted(
        p for p in documents_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def main() -> int:
    if not DOCUMENTS_DIR.exists():
        print(f"ERROR: '{DOCUMENTS_DIR}/' does not exist.", file=sys.stderr)
        return 1

    files = discover_files(DOCUMENTS_DIR)
    if not files:
        print(
            f"No supported files found in '{DOCUMENTS_DIR}/'.\n"
            f"Save your sources there as: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        return 1

    all_chunks: list[Chunk] = []
    print(f"Ingesting {len(files)} file(s) from '{DOCUMENTS_DIR}/'\n")
    for path in files:
        try:
            chunks = build_chunks_for_file(path)
        except Exception as exc:  # one bad file shouldn't kill the whole run
            print(f"  ! SKIPPED {path.name}: {exc}", file=sys.stderr)
            continue
        all_chunks.extend(chunks)
        words = sum(c.word_count for c in chunks)
        print(f"  ✓ {path.name:40} {len(chunks):3} chunks  ({words} words)")

    if not all_chunks:
        print("\nNo chunks produced — nothing written.", file=sys.stderr)
        return 1

    OUTPUT_FILE.write_text(
        json.dumps([asdict(c) for c in all_chunks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts = [c.word_count for c in all_chunks]
    print(
        f"\nDone. {len(all_chunks)} chunks from {len(files)} files "
        f"-> {OUTPUT_FILE}\n"
        f"  config:     chunk_size={CHUNK_SIZE}w  overlap={OVERLAP}w\n"
        f"  word count: min={min(counts)}  max={max(counts)}  "
        f"avg={sum(counts) // len(counts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
