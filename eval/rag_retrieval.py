# rag_retrieval.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
import numpy as np

import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv
import os

EMBED_MODEL = "text-embedding-3-small"


@dataclass
class Retrieved:
    doc: str
    meta: Dict[str, Any]
    distance: float
    embedding: Optional[List[float]] = None  # only when include=["embeddings"]

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)

def mmr_select(
    query_emb: np.ndarray,
    cand_embs: np.ndarray,
    *,
    top_k: int,
    lambda_mult: float = 0.5,
) -> List[int]:
    """
    MMR: maximize λ * sim(query, doc) - (1-λ) * max_{selected} sim(doc, selected)
    Returns selected indices in candidate list.
    """
    n = cand_embs.shape[0]
    if n == 0:
        return []
    top_k = min(top_k, n)

    # Similarity to query
    sim_q = np.array([_cosine_sim(query_emb, cand_embs[i]) for i in range(n)], dtype=float)

    selected: List[int] = []
    remaining = set(range(n))

    # pick the best first
    first = int(np.argmax(sim_q))
    selected.append(first)
    remaining.remove(first)

    while len(selected) < top_k and remaining:
        best_i = None
        best_score = -1e18
        for i in remaining:
            # diversity penalty: similarity to already selected
            sim_to_sel = max(_cosine_sim(cand_embs[i], cand_embs[j]) for j in selected)
            score = lambda_mult * sim_q[i] - (1.0 - lambda_mult) * sim_to_sel
            if score > best_score:
                best_score = score
                best_i = i
        selected.append(best_i)
        remaining.remove(best_i)

    return selected

class Retriever:
    def __init__(self, *, chroma_dir: str, collection_name: str):
        load_dotenv() 
        self._openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chroma = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.col = self.chroma.get_collection(name=collection_name)

    def query(
        self,
        *,
        query_embedding: List[float],
        top_k: int = 5,
        method: str = "topk",   # "topk" or "mmr"
        fetch_k: int = 25,      # only for mmr (initial candidate size)
        lambda_mult: float = 0.5,
        # --- NEW ---
        min_page_start: int = 3,          # 1-2ページを除外するなら3
        restrict_source: Optional[str] = None,  # 特定PDFに絞りたい時（任意）
    ) -> List[Retrieved]:
        if method not in ("topk", "mmr"):
            raise ValueError("method must be 'topk' or 'mmr'")

        # --- NEW: where filter ---
        where: Dict[str, Any] = {"page_start": {"$gte": min_page_start}}
        if restrict_source:
            where["source"] = restrict_source

        if method == "topk":
            res = self.col.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,  # ★追加
                include=["documents", "metadatas", "distances"],
            )
            return [
                Retrieved(d, m, dist)
                for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
            ]

        # mmr: fetch more, then diversify
        res = self.col.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            where=where,  # ★追加
            include=["documents", "metadatas", "distances", "embeddings"],
        )
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        embs = res["embeddings"][0]  # list[list[float]]

        q = np.array(query_embedding, dtype=float)
        C = np.array(embs, dtype=float)

        sel_idx = mmr_select(q, C, top_k=top_k, lambda_mult=lambda_mult)

        out: List[Retrieved] = []
        for i in sel_idx:
            out.append(Retrieved(docs[i], metas[i], dists[i], embs[i]))
        return out

    def _embed_query(self, query: str) -> List[float]:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set (.env を確認してください)")

        client = OpenAI(api_key=api_key)
        return client.embeddings.create(model=EMBED_MODEL, input=query).data[0].embedding

    def retrieve(
        self,
        query: str,
        *,
        method: str = "topk",
        top_k: int = 7,
        fetch_k: int = 30,
        lam: float = 0.9,
        # --- NEW ---
        min_page_start: int = 3,
        restrict_source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q_emb = self._embed_query(query)

        hits = self.query(
            query_embedding=q_emb,
            top_k=top_k,
            method=method,
            fetch_k=fetch_k,
            lambda_mult=lam,
            # --- NEW ---
            min_page_start=min_page_start,
            restrict_source=restrict_source,
        )

        out: List[Dict[str, Any]] = []
        for r in hits:
            out.append(
                {
                    "text": r.doc,
                    "metadata": r.meta,
                    "distance": r.distance,
                }
            )
        return out


