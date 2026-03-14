from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from internal_llm.evaluation.meeting_structuring import run_meeting_structuring_eval


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True, help="outputs/*.summary.json")
    ap.add_argument("--out_json", default=None)
    ap.add_argument("--out_md", default=None)
    args = ap.parse_args()

    summary_path = Path(args.summary)
    out_json = Path(args.out_json) if args.out_json else summary_path.with_suffix(".eval.json")
    out_md = Path(args.out_md) if args.out_md else summary_path.with_suffix(".eval.md")

    out_json_path, out_md_path = run_meeting_structuring_eval(summary_path, out_json, out_md)
    print(f"OK: {out_json_path}")
    print(f"OK: {out_md_path}")


if __name__ == "__main__":
    main()
