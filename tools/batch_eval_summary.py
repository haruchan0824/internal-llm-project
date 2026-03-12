# tools/batch_eval_summary.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

def load_eval(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def fmt(x):
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="real_*.summary.eval.json", help="glob in outputs/")
    ap.add_argument("--out", default=str(OUTPUTS_DIR / "batch_eval_summary.md"))
    args = ap.parse_args()

    files = sorted(OUTPUTS_DIR.glob(args.pattern))
    if not files:
        raise SystemExit(f"No eval files matched: outputs/{args.pattern}")

    rows = []
    for f in files:
        d = load_eval(f)
        m = d.get("metrics", {})
        if m.get("schema_type") != "global":
            continue

        rows.append({
            "file": Path(d.get("file", f.name)).name,
            "issues_cnt": m.get("issues_cnt", 0),
            "open_questions_cnt": m.get("open_questions_cnt", 0),
            "next_actions_cnt": m.get("next_actions_cnt", 0),
            "decisions_cnt": m.get("decisions_cnt", 0),
            "owner_rate": m.get("action_owner_filled_rate", 0.0),
            "due_rate": m.get("action_due_filled_rate", 0.0),
            "due_missing_cnt": m.get("action_due_missing_cnt", None),
            "speculation_flag": m.get("speculation_flag", False),
        })

    if not rows:
        raise SystemExit("No global-schema evals found.")

    # summary stats
    def col(name):
        return [r[name] for r in rows if r[name] is not None]

    issues = col("issues_cnt")
    oq = col("open_questions_cnt")
    acts = col("next_actions_cnt")
    decs = col("decisions_cnt")
    owner = col("owner_rate")
    due = col("due_rate")

    md = []
    md.append("# Batch Eval Summary (Meeting Structuring)")
    md.append("")
    md.append(f"- files: {len(rows)}")
    md.append("")
    md.append("## Aggregate (mean / min / max)")
    md.append("")
    md.append("| metric | mean | min | max |")
    md.append("|---|---:|---:|---:|")
    md.append(f"| issues_cnt | {fmt(mean(issues))} | {min(issues)} | {max(issues)} |")
    md.append(f"| open_questions_cnt | {fmt(mean(oq))} | {min(oq)} | {max(oq)} |")
    md.append(f"| next_actions_cnt | {fmt(mean(acts))} | {min(acts)} | {max(acts)} |")
    md.append(f"| decisions_cnt | {fmt(mean(decs))} | {min(decs)} | {max(decs)} |")
    md.append(f"| action_owner_filled_rate | {fmt(mean(owner))} | {fmt(min(owner))} | {fmt(max(owner))} |")
    md.append(f"| action_due_filled_rate | {fmt(mean(due))} | {fmt(min(due))} | {fmt(max(due))} |")
    md.append("")

    md.append("## Per-file")
    md.append("")
    md.append("| file | issues | openQ | actions | decisions | owner_rate | due_rate | due_missing_cnt | speculation |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows:
        md.append(
            f"| {r['file']} | {r['issues_cnt']} | {r['open_questions_cnt']} | {r['next_actions_cnt']} | {r['decisions_cnt']} "
            f"| {fmt(r['owner_rate'])} | {fmt(r['due_rate'])} | {r['due_missing_cnt']} | {r['speculation_flag']} |"
        )
    md.append("")
    md.append("## Notes")
    md.append("- High open_questions_cnt is expected for thin meeting minutes; it indicates unknowns are captured instead of hallucinated.")
    md.append("- due_rate can be low when minutes omit deadlines; we intentionally avoid guessing deadlines (safety-first).")
    md.append("")

    out = Path(args.out)
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"OK: {out}")

if __name__ == "__main__":
    main()
