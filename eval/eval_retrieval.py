# eval_retrieval.py
from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any, Dict, List
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_retrieval import Retriever
from internal_llm.utils.config import get_config_value, load_project_config
import re

def norm_source(x):
    if x is None:
        return None
    x = str(x)
    return x.split("\\")[-1].split("/")[-1]

def to_int(x):
    if x is None:
        return None
    try:
        return int(x)
    except Exception:
        m = re.search(r"\d+", str(x))
        return int(m.group()) if m else None

def get_meta_source_page_range(md: dict):
    src = md.get("source") or md.get("source_name") or md.get("file") or md.get("filename")
    src = norm_source(src)

    # ★ここが重要：page_start / page_end を優先
    ps = md.get("page_start")
    pe = md.get("page_end")

    if ps is None and pe is None:
        # 互換：page単体しかない場合も拾う
        p = md.get("page") or md.get("page_num") or md.get("page_number") or md.get("page_index")
        p = to_int(p)
        if p is None:
            return src, None, None
        # page_index 0始まりの可能性もあるので両方許容するためにレンジ化
        return src, p, p

    return src, to_int(ps), to_int(pe)

# --- Paths (絶対パスで事故防止) ---
EVAL_DIR = PROJECT_ROOT / "eval"
DEFAULT_QSET_PATH = EVAL_DIR / "qset.jsonl"

_paths_cfg = load_project_config(PROJECT_ROOT, "configs/paths.yaml")
_retrieval_cfg = load_project_config(PROJECT_ROOT, "configs/retrieval.yaml")

DEFAULT_CHROMA_DIR = PROJECT_ROOT / get_config_value(_paths_cfg, ["paths", "chroma_dir"], "data/chroma")
DEFAULT_COLLECTION = get_config_value(_retrieval_cfg, ["retrieval", "default_collection"], "pdf_chunks_v1")
DEFAULT_TOP_K = int(get_config_value(_retrieval_cfg, ["retrieval", "default_top_k"], 7))
DEFAULT_FETCH_K = int(get_config_value(_retrieval_cfg, ["retrieval", "default_fetch_k"], 30))
DEFAULT_LAM = float(get_config_value(_retrieval_cfg, ["retrieval", "default_lam"], 0.9))


def load_qset(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Qset not found: {path}")
    qset = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            qset.append(json.loads(line))
    if not qset:
        raise RuntimeError(f"Qset is empty: {path}")
    return qset


def eval_once(
    *,
    chroma_dir: str,
    collection_name: str,
    qset_path: Path,
    method: str,
    top_k: int,
    fetch_k: int,
    lam: float,
) -> Dict[str, float]:
    qset = load_qset(qset_path)

    retriever = Retriever(chroma_dir=chroma_dir, collection_name=collection_name)

    hits = 0
    rr_sum = 0.0

    for item in qset:
        q = item["question"]
        gold_list = item.get("gold", [])

        # --- goldを (source, page) の集合にする ---
        gold_pairs = set()
        for g in gold_list:
            src = g.get("source")
            page = g.get("page")
            if src is None or page is None:
                continue
            gold_pairs.add((str(src), int(page)))

        # --- ここで検索を実行（results を作る） ---
        results = retriever.retrieve(
            q,
            method=method,
            top_k=top_k,
            fetch_k=fetch_k,
            lam=lam,
        )

        # --- 検索結果から (source, page_start, page_end) を見てヒット判定 ---
        found_rank = None
        for rank, r in enumerate(results, start=1):
            md = r.get("metadata") or {}
            src = md.get("source")
            ps = md.get("page_start")
            pe = md.get("page_end")

            if src is None or ps is None or pe is None:
                continue

            src = str(src)
            ps = int(ps)
            pe = int(pe)

            for (gsrc, gpage) in gold_pairs:
                if src == gsrc and ps <= gpage <= pe:
                    found_rank = rank
                    break

            if found_rank is not None:
                break

        if found_rank is not None:
            hits += 1
            rr_sum += 1.0 / found_rank



    n = len(qset)
    return {
        "n": float(n),
        "hit@k": hits / n,
        "mrr": rr_sum / n,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate retrieval with Hit@k and MRR.")
    p.add_argument("--qset", type=str, default=str(DEFAULT_QSET_PATH), help="Path to qset.jsonl")
    p.add_argument("--chroma_dir", type=str, default=str(DEFAULT_CHROMA_DIR), help="Chroma persist dir")
    p.add_argument("--collection", type=str, default=DEFAULT_COLLECTION, help="Chroma collection name")

    # 実行モード（単発 or 2方式比較）
    p.add_argument(
        "--mode",
        type=str,
        default="compare",
        choices=["single", "compare"],
        help="single: evaluate one method. compare: evaluate topk and mmr.",
    )

    # method params
    p.add_argument("--method", type=str, default="topk", choices=["topk", "mmr"], help="Used when mode=single")
    p.add_argument("--top_k", type=int, default=DEFAULT_TOP_K, help="Top-k to return")
    p.add_argument("--fetch_k", type=int, default=DEFAULT_FETCH_K, help="MMR candidate pool size (only for mmr)")
    p.add_argument("--lam", type=float, default=DEFAULT_LAM, help="MMR lambda (only for mmr)")

    return p.parse_args()


def main():
    args = parse_args()

    qset_path = Path(args.qset).resolve()

    if args.mode == "single":
        out = eval_once(
            chroma_dir=args.chroma_dir,
            collection_name=args.collection,
            qset_path=qset_path,
            method=args.method,
            top_k=args.top_k,
            fetch_k=args.fetch_k,
            lam=args.lam,
        )
        print(
            f"{args.method.upper()}: collection={args.collection} top_k={args.top_k} fetch_k={args.fetch_k} lam={args.lam}"
        )
        print(out)
        return

    # compare mode
    topk_out = eval_once(
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
        qset_path=qset_path,
        method="topk",
        top_k=args.top_k,
        fetch_k=0,
        lam=0.0,
    )
    mmr_out = eval_once(
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
        qset_path=qset_path,
        method="mmr",
        top_k=args.top_k,
        fetch_k=args.fetch_k,
        lam=args.lam,
    )

    print(f"COLLECTION: {args.collection}")
    print(f"TOPK (k={args.top_k}): {topk_out}")
    print(f"MMR  (k={args.top_k}, fetch_k={args.fetch_k}, lam={args.lam}): {mmr_out}")


if __name__ == "__main__":
    main()

