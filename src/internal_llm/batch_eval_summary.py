from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


def load_eval(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def collect_global_rows(files: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file_path in files:
        data = load_eval(file_path)
        metrics = data.get("metrics", {})
        if metrics.get("schema_type") != "global":
            continue

        rows.append(
            {
                "file": Path(data.get("file", file_path.name)).name,
                "issues_cnt": metrics.get("issues_cnt", 0),
                "open_questions_cnt": metrics.get("open_questions_cnt", 0),
                "next_actions_cnt": metrics.get("next_actions_cnt", 0),
                "decisions_cnt": metrics.get("decisions_cnt", 0),
                "owner_rate": metrics.get("action_owner_filled_rate", 0.0),
                "due_rate": metrics.get("action_due_filled_rate", 0.0),
                "due_missing_cnt": metrics.get("action_due_missing_cnt", None),
                "speculation_flag": metrics.get("speculation_flag", False),
            }
        )
    return rows


def render_batch_eval_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        raise ValueError("No global-schema evals found.")

    def col(name: str) -> list[Any]:
        return [row[name] for row in rows if row[name] is not None]

    issues = col("issues_cnt")
    open_questions = col("open_questions_cnt")
    actions = col("next_actions_cnt")
    decisions = col("decisions_cnt")
    owner_rates = col("owner_rate")
    due_rates = col("due_rate")

    md: list[str] = []
    md.append("# Batch Eval Summary (Meeting Structuring)")
    md.append("")
    md.append(f"- files: {len(rows)}")
    md.append("")
    md.append("## Aggregate (mean / min / max)")
    md.append("")
    md.append("| metric | mean | min | max |")
    md.append("|---|---:|---:|---:|")
    md.append(f"| issues_cnt | {fmt(mean(issues))} | {min(issues)} | {max(issues)} |")
    md.append(f"| open_questions_cnt | {fmt(mean(open_questions))} | {min(open_questions)} | {max(open_questions)} |")
    md.append(f"| next_actions_cnt | {fmt(mean(actions))} | {min(actions)} | {max(actions)} |")
    md.append(f"| decisions_cnt | {fmt(mean(decisions))} | {min(decisions)} | {max(decisions)} |")
    md.append(
        f"| action_owner_filled_rate | {fmt(mean(owner_rates))} | {fmt(min(owner_rates))} | {fmt(max(owner_rates))} |"
    )
    md.append(f"| action_due_filled_rate | {fmt(mean(due_rates))} | {fmt(min(due_rates))} | {fmt(max(due_rates))} |")
    md.append("")

    md.append("## Per-file")
    md.append("")
    md.append("| file | issues | openQ | actions | decisions | owner_rate | due_rate | due_missing_cnt | speculation |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in rows:
        md.append(
            f"| {row['file']} | {row['issues_cnt']} | {row['open_questions_cnt']} | {row['next_actions_cnt']} | {row['decisions_cnt']} "
            f"| {fmt(row['owner_rate'])} | {fmt(row['due_rate'])} | {row['due_missing_cnt']} | {row['speculation_flag']} |"
        )
    md.append("")
    md.append("## Notes")
    md.append(
        "- High open_questions_cnt is expected for thin meeting minutes; it indicates unknowns are captured instead of hallucinated."
    )
    md.append(
        "- due_rate can be low when minutes omit deadlines; we intentionally avoid guessing deadlines (safety-first)."
    )
    md.append("")
    return "\n".join(md)


def write_batch_eval_summary(*, outputs_dir: Path, pattern: str, out_path: Path) -> Path:
    files = sorted(outputs_dir.glob(pattern))
    if not files:
        raise ValueError(f"No eval files matched: {outputs_dir.name}/{pattern}")

    rows = collect_global_rows(files)
    markdown = render_batch_eval_summary(rows)
    out_path.write_text(markdown, encoding="utf-8")
    return out_path
