from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from internal_llm.batch_eval_summary import write_batch_eval_summary

OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="real_*.summary.eval.json", help="glob in outputs/")
    ap.add_argument("--out", default=str(OUTPUTS_DIR / "batch_eval_summary.md"))
    args = ap.parse_args()

    out_path = write_batch_eval_summary(
        outputs_dir=OUTPUTS_DIR,
        pattern=args.pattern,
        out_path=Path(args.out),
    )
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
