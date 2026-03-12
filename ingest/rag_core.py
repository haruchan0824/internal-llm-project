# rag_core.py
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import List, Dict, Any, Iterable, Tuple

from pypdf import PdfReader

# ---- Data structures ----
@dataclass
class PageText:
    page: int              # 1-indexed
    text: str
    heading: str           # best-effort inferred heading


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: Dict[str, Any]  # {source, page_start, page_end, heading}


# ---- PDF extraction ----
_HEADING_PATTERNS = [
    re.compile(r"^\s*(\d+(\.\d+)*)\s+.+$"),          # "1.2 Title"
    re.compile(r"^\s*第[一二三四五六七八九十百千]+[章節]\s*.*$"),  # "第X章 ..."
    re.compile(r"^\s*[A-Z][A-Z0-9 \-\:]{6,}\s*$"),   # ALLCAPS-ish headings
]

def infer_heading(lines: List[str], prev_heading: str) -> str:
    """
    Best-effort heading inference from page lines.
    Keeps last known heading if nothing looks like a heading.
    """
    for line in lines[:25]:  # look only at top region
        s = line.strip()
        if not s:
            continue
        if any(p.match(s) for p in _HEADING_PATTERNS):
            return s[:120]
    return prev_heading


def extract_pdf_pages(pdf_path: str, source_name: str | None = None) -> List[PageText]:
    reader = PdfReader(pdf_path)
    pages: List[PageText] = []
    heading = "UNKNOWN"

    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        # normalize whitespace a bit
        raw = re.sub(r"\u00a0", " ", raw)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw).strip()

        lines = raw.splitlines()
        heading = infer_heading(lines, heading)

        pages.append(PageText(
            page=i + 1,
            text=raw,
            heading=heading,
        ))
    return pages


# ---- Chunking ----
def chunk_text(
    text: str,
    *,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Simple character-based chunking (Week1 minimal).
    Later you can replace with token-based chunking (tiktoken) for better control.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be < chunk_size")

    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - chunk_overlap

    return chunks


def pages_to_chunks(
    pages: List[PageText],
    *,
    source: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> List[Chunk]:
    out: List[Chunk] = []
    idx = 0

    for p in pages:
        parts = chunk_text(p.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for part in parts:
            idx += 1
            out.append(Chunk(
                chunk_id=f"{source}::p{p.page:04d}::c{idx:06d}",
                text=part,
                metadata={
                    "source": source,
                    "page_start": p.page,
                    "page_end": p.page,
                    "heading": p.heading,
                }
            ))
    return out


# ---- Citation formatting ----
def format_citations(metadatas: List[Dict[str, Any]]) -> str:
    """
    Make a compact citations string from retrieved metadatas.
    """
    # unique while preserving order
    seen = set()
    cites = []
    for md in metadatas:
        key = (md.get("source"), md.get("page_start"), md.get("page_end"), md.get("heading"))
        if key in seen:
            continue
        seen.add(key)
        source = md.get("source", "UNKNOWN")
        ps = md.get("page_start", "?")
        pe = md.get("page_end", ps)
        heading = md.get("heading", "UNKNOWN")
        if ps == pe:
            cites.append(f"- {source} p.{ps} / {heading}")
        else:
            cites.append(f"- {source} p.{ps}-{pe} / {heading}")
    return "\n".join(cites)
