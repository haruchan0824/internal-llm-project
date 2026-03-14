# tools/run_meeting_batch.py
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from internal_llm.utils.config import get_config_value, load_project_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_paths_cfg = load_project_config(PROJECT_ROOT, "configs/paths.yaml")
_meeting_cfg = load_project_config(PROJECT_ROOT, "configs/meeting.yaml")

MEETINGS_DIR = PROJECT_ROOT / "meetings"
OUTPUTS_DIR = PROJECT_ROOT / str(get_config_value(_paths_cfg, ["paths", "outputs_dir"], "outputs"))
DEFAULT_MODEL = get_config_value(_meeting_cfg, ["meeting", "default_model"], "gpt-4.1-mini")
DEFAULT_INCLUDE_TABLES = bool(get_config_value(_meeting_cfg, ["meeting", "include_tables"], False))
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def run(cmd: list[str]) -> None:
    # 先頭が "python" でも "py" でも、必ず “今動いているpython(=venv)” で実行する
    fixed = [sys.executable] + cmd[1:]
    print(">", " ".join(fixed))
    subprocess.check_call(fixed)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="real_*", help="glob in meetings/ (default: real_*)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max_n", type=int, default=5)
    ap.add_argument("--include_tables", action="store_true", default=DEFAULT_INCLUDE_TABLES)
    args = ap.parse_args()

    files = sorted(MEETINGS_DIR.glob(args.pattern + ".*"))
    files = [p for p in files if p.suffix.lower() in (".md", ".txt", ".docx")]
    files = files[: args.max_n]

    if not files:
        raise SystemExit(f"No meeting files found in {MEETINGS_DIR} with pattern {args.pattern}.*")

    batch_md_lines = ["# Batch Eval (Meeting Structuring)", ""]

    for p in files:
        # 1) summarize
        cmd = ["python", "meeting_summary/summarize_meeting.py", "--input", str(p), "--model", args.model]
        if args.include_tables:
            cmd.append("--include_tables")
        run(cmd)

        # output path (summarize_meeting.py の default_out_path に合わせる)
        summary = OUTPUTS_DIR / f"{p.stem}.summary.json"

        # 2) eval
        run(["python", "meeting_summary/eval_meeting_structuring.py", "--summary", str(summary)])

        eval_md = OUTPUTS_DIR / f"{p.stem}.summary.eval.md"
        if eval_md.exists():
            batch_md_lines.append(eval_md.read_text(encoding="utf-8"))
            batch_md_lines.append("\n---\n")

    batch_path = OUTPUTS_DIR / "batch_eval.md"
    batch_path.write_text("\n".join(batch_md_lines), encoding="utf-8")
    print(f"OK: {batch_path}")

if __name__ == "__main__":
    main()
