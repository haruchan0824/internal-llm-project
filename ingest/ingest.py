# ingest.py
from __future__ import annotations

import os
import glob
import argparse
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from rag_core import extract_pdf_pages, pages_to_chunks

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Put it in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

# 既存の値（元コード）をベースにしつつ、引数で上書きします
CHROMA_DIR = "data/chroma"
EMBED_MODEL = "text-embedding-3-small"


def embed_texts(texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest PDFs into Chroma with configurable chunking.")
    p.add_argument("--chroma_dir", type=str, default=CHROMA_DIR, help="Chroma persist dir (default: data/chroma)")
    p.add_argument("--chunk_size", type=int, default=1200, help="Chunk size (characters).")
    p.add_argument("--chunk_overlap", type=int, default=200, help="Chunk overlap (characters).")
    p.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Collection name. If omitted, auto = pdf_chunks_cs{chunk_size}_co{chunk_overlap}",
    )
    p.add_argument("--pdf_glob", type=str, default="pdfs/*.pdf", help="PDF glob pattern (default: pdfs/*.pdf)")
    p.add_argument("--batch", type=int, default=64, help="Embedding batch size (default: 64)")
    return p.parse_args()


def main():
    args = parse_args()

    # ★ chunk設定ごとにコレクションを分ける（上書き事故防止）
    collection_name = args.collection or f"pdf_chunks_cs{args.chunk_size}_co{args.chunk_overlap}"

    os.makedirs(args.chroma_dir, exist_ok=True)

    chroma = chromadb.PersistentClient(
        path=args.chroma_dir,
        settings=Settings(anonymized_telemetry=False),
    )
    col = chroma.get_or_create_collection(name=collection_name)

    pdf_paths = sorted(glob.glob(args.pdf_glob))
    if not pdf_paths:
        raise RuntimeError(f"No PDFs found. glob={args.pdf_glob}")

    for pdf_path in pdf_paths:
        source = os.path.basename(pdf_path)
        pages = extract_pdf_pages(pdf_path, source_name=source)

        # ★ ここが chunk長対応（元コードは 1200/200 固定）:contentReference[oaicite:1]{index=1}
        chunks = pages_to_chunks(
            pages,
            source=source,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )

        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        metas = [c.metadata for c in chunks]

        for i in range(0, len(texts), args.batch):
            t_batch = texts[i : i + args.batch]
            id_batch = ids[i : i + args.batch]
            m_batch = metas[i : i + args.batch]

            embs = embed_texts(t_batch)
            col.add(
                ids=id_batch,
                documents=t_batch,
                metadatas=m_batch,
                embeddings=embs,
            )

        print(f"[OK] Ingested: {source} (chunks={len(chunks)})")

    print(f"\nDone. Chroma persisted at: {args.chroma_dir} / collection={collection_name}")
    print(f"Chunking: chunk_size={args.chunk_size}, chunk_overlap={args.chunk_overlap}")


if __name__ == "__main__":
    main()
