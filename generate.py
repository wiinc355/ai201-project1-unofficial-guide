"""
Milestone 5a — Answer generation (RAG)
The Unofficial Guide: Student Technology Survival Guide

Ties retrieval to generation:
  1. RETRIEVE the top-k chunks for the question (retrieve.search)
  2. BUILD    a grounded prompt containing those chunks, each tagged with its
             source file so the model can cite where each fact came from
  3. GENERATE the final answer with the Groq API

This directly addresses planning.md > Anticipated Challenges: the model is told
to answer ONLY from the retrieved context and to cite the source file, so users
can verify the information (source attribution).

Use as a library (the Streamlit app calls answer()):
    from generate import answer
    result = answer("How do I reset my password?")
    print(result.text)        # the answer
    print(result.hits)        # the chunks it was grounded on

Or from the command line:
    python generate.py "How do I enroll in MFA?"
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

from retrieve import Hit, search

load_dotenv()  # read GROQ_API_KEY (and optional GROQ_MODEL) from .env

# A current Groq production model. Override in .env with GROQ_MODEL=...
# See https://console.groq.com/docs/models for the live list.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = (
    "You are the Student Technology Survival Guide, an assistant that helps "
    "students with campus technology questions (Wi-Fi, passwords, Microsoft 365, "
    "MFA, Canvas, printing, laptops, and IT policies).\n\n"
    "Rules:\n"
    "1. Answer the question using ONLY the information in the numbered sources "
    "provided in the context. Do not use any outside or prior knowledge.\n"
    "2. After each fact, cite the source it came from like this: [Source 2].\n"
    "3. If the sources do not contain enough information to answer, reply exactly: "
    "\"I don't have enough information on that.\" and suggest contacting the IT "
    "Help Desk. Do not guess or invent details.\n"
    "4. Be concise and use steps when describing a procedure."
)


@dataclass
class Answer:
    text: str          # the generated answer
    hits: list[Hit]    # the retrieved chunks used as context
    model: str         # which Groq model produced it

    @property
    def sources(self) -> list[str]:
        """
        The source documents this answer was built from — derived
        PROGRAMMATICALLY from the retrieved chunks, NOT from anything the LLM
        wrote. This guarantees attribution even if the model forgets to cite.
        Deduplicated, preserving retrieval (best-first) order.
        """
        seen: dict[str, None] = {}
        for h in self.hits:
            seen.setdefault(h.source_file, None)
        return list(seen)


def build_context(hits: list[Hit]) -> str:
    """Format retrieved chunks as a numbered, source-labeled context block."""
    blocks = []
    for h in hits:
        blocks.append(f"[Source {h.rank}] ({h.source_file})\n{h.text}")
    return "\n\n".join(blocks)


def answer(query: str, top_k: int = 5) -> Answer:
    """Retrieve context for `query` and generate a grounded, cited answer."""
    hits = search(query, top_k=top_k)

    if not hits:
        return Answer(
            text=(
                "I couldn't find anything relevant in the guide. Make sure the "
                "index is built (`python embed.py`), or contact the IT Help Desk."
            ),
            hits=[],
            model=GROQ_MODEL,
        )

    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add your key to .env "
            "(get a free one at https://console.groq.com)."
        )

    from groq import Groq

    client = Groq()  # reads GROQ_API_KEY from the environment
    user_message = (
        f"Context:\n{build_context(hits)}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the sources above and cite them."
    )

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,  # low — we want faithful, not creative, answers
    )

    return Answer(
        text=completion.choices[0].message.content,
        hits=hits,
        model=GROQ_MODEL,
    )


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python generate.py "your question"', file=sys.stderr)
        return 1

    result = answer(" ".join(sys.argv[1:]))
    print(result.text)
    # Programmatically appended source list — guaranteed, not LLM-dependent.
    print("\n" + "-" * 60 + "\nSources (retrieved from):")
    for s in result.sources:
        print(f"  • {s}")
    print("\nChunk detail:")
    for h in result.hits:
        print(f"  [Source {h.rank}] {h.source_file} "
              f"(chunk {h.chunk_index}, sim={h.similarity})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
