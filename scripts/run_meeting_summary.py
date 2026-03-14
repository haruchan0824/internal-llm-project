from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from internal_llm.meeting.summarize import run_meeting_summary
from internal_llm.utils.config import get_config_value, load_project_config


def main() -> None:
    meeting_cfg = load_project_config(PROJECT_ROOT, "configs/meeting.yaml")
    default_model = get_config_value(meeting_cfg, ["meeting", "default_model"], "gpt-4.1-mini")
    default_include_tables = bool(get_config_value(meeting_cfg, ["meeting", "include_tables"], False))

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="meetings/*.md or *.docx")
    parser.add_argument("--model", default=default_model, help="chat model name")
    parser.add_argument("--out", default=None, help="output json path (optional)")
    parser.add_argument("--include_tables", action="store_true", default=default_include_tables, help="include tables in docx extraction")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else None
    result_path = run_meeting_summary(
        project_root=PROJECT_ROOT,
        input_path=args.input,
        model=args.model,
        out_path=out_path,
        include_tables=args.include_tables,
    )
    print(f"OK: {result_path}")


if __name__ == "__main__":
    main()
