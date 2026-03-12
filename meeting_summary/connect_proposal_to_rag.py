# meeting_summary/connect_proposal_to_rag.py
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# --- import Retriever safely (project layout friendly) ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # .../pdf_rag
EVAL_DIR = PROJECT_ROOT / "eval"

import sys
sys.path.insert(0, str(EVAL_DIR))  # so we can import eval/rag_retrieval.py as a module

from rag_retrieval import Retriever  # noqa: E402


def load_summary_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_query(proposal_point: str) -> str:
    # 「営業の主張」を作るのではなく「根拠を探す」ための問い合わせに固定
    return (
        f"次の提案方針に関する技術的根拠（仕様・特性・注意点）を技術資料から探してください。\n"
        f"提案方針: {proposal_point}\n"
        f"関連しそうなキーワード（例：耐久性、耐候性、構造、施工、用途、適用条件）が含まれる箇所を優先してください。"
    )


def format_evidence_item(d: Dict[str, Any], *, excerpt_chars: int) -> Dict[str, Any]:
    md = d.get("metadata") or {}
    text = d.get("text") or ""
    return {
        "source": md.get("source"),
        "page_start": md.get("page_start"),
        "page_end": md.get("page_end"),
        "heading": md.get("heading"),
        "distance": d.get("distance"),
        "excerpt": text[:excerpt_chars],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True, help="構造化要約JSONのパス（*.summary.json）")
    parser.add_argument("--collection", required=True, help="技術資料Chromaコレクション名")
    parser.add_argument("--top_k", type=int, default=7)
    parser.add_argument("--method", choices=["topk", "mmr"], default="topk")
    parser.add_argument("--fetch_k", type=int, default=30)
    parser.add_argument("--lam", type=float, default=0.9)
    parser.add_argument("--chroma_dir", default=str(PROJECT_ROOT / "data"/"chroma"))
    parser.add_argument("--out_dir", default=str(PROJECT_ROOT / "outputs"))
    parser.add_argument("--excerpt_chars", type=int, default=320)
    args = parser.parse_args()

    load_dotenv()

    summary_path = Path(args.summary)
    if not summary_path.exists():
        raise FileNotFoundError(f"summary not found: {summary_path}")

    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)

    summary = load_summary_json(summary_path)
    proposal_points: List[str] = summary.get("proposal_directions") or []
    if not proposal_points:
        raise ValueError("summary JSON に proposal_directions が見つかりません（空です）")

    # Retriever init
    retriever = Retriever(
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
    )

    outputs: Dict[str, Any] = {
        "summary_file": str(summary_path),
        "collection": args.collection,
        "method": args.method,
        "top_k": args.top_k,
        "fetch_k": args.fetch_k,
        "lam": args.lam,
        "items": [],
    }

    for point in proposal_points:
        q = build_query(point)

        docs = retriever.retrieve(
            q,
            method=args.method,
            top_k=args.top_k,
            fetch_k=args.fetch_k if args.method == "mmr" else 0,
            lam=args.lam if args.method == "mmr" else 0.0,
        )

        item = {
            "proposal_point": point,
            "query": q,
            "evidences": [format_evidence_item(d, excerpt_chars=args.excerpt_chars) for d in docs],
        }
        outputs["items"].append(item)

        # console preview (short)
        print("\n=== proposal_point ===")
        print(point)
        print("top evidence:", item["evidences"][0]["source"], item["evidences"][0]["page_start"], "-", item["evidences"][0]["page_end"])

    out_path = out_dir / f"{summary_path.stem}.proposal_support.json"
    out_path.write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nOK:", out_path)


if __name__ == "__main__":
    main()
