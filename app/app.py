# app.py
from __future__ import annotations
import os
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings

from openai import OpenAI

from rag_core import format_citations

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Put it in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "pdf_chunks_v1"
EMBED_MODEL = "text-embedding-3-small"

# You can switch models here.
GEN_MODEL = "gpt-4o-mini"

def embed_query(q: str) -> list[float]:
    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=q,
    )
    return resp.data[0].embedding

def retrieve(q: str, *, top_k: int = 5):
    chroma = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    col = chroma.get_collection(name=COLLECTION_NAME)

    q_emb = embed_query(q)
    res = col.query(
        query_embeddings=[q_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    return docs, metas, dists

def build_context(docs: list[str], metas: list[dict]) -> str:
    """
    Build a context block with explicit source tags so the model can cite.
    """
    blocks = []
    for i, (doc, md) in enumerate(zip(docs, metas), start=1):
        src = md.get("source", "UNKNOWN")
        ps = md.get("page_start", "?")
        pe = md.get("page_end", ps)
        heading = md.get("heading", "UNKNOWN")
        tag = f"[S{i}] {src} p.{ps}-{pe} / {heading}"
        blocks.append(tag + "\n" + doc.strip())
    return "\n\n---\n\n".join(blocks)

def answer(question: str, *, top_k: int = 5) -> str:
    docs, metas, _ = retrieve(question, top_k=top_k)
    context = build_context(docs, metas)

    system = (
        "You are a careful assistant for internal technical documents.\n"
        "Rules:\n"
        "1) Use ONLY the provided context to answer.\n"
        "2) If the answer is not in the context, say you don't know.\n"
        "3) Always include citations in the form (S1), (S2) referring to the context blocks.\n"
        "4) Keep it concise: conclusion first, then brief explanation.\n"
    )

    # Responses API reference: :contentReference[oaicite:7]{index=7}
    resp = client.responses.create(
        model=GEN_MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"},
        ],
        # data controls / store parameter: :contentReference[oaicite:8]{index=8}
        store=False,
    )

    citations = format_citations(metas)
    return f"{resp.output_text}\n\n---\nCitations:\n{citations}"

def cli():
    print("PDF RAG (Week1). Type a question. Ctrl+C to exit.\n")
    while True:
        q = input("Q> ").strip()
        if not q:
            continue
        out = answer(q, top_k=5)
        print("\nA>\n" + out + "\n")

if __name__ == "__main__":
    cli()
