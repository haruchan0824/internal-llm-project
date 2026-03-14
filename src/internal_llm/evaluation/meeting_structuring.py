from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ざっくり「推測っぽい表現」検知（完全ではないが安全側に倒す）
SPECULATION_PATTERNS = [
    r"と思われる", r"と考えられる", r"推測", r"おそらく", r"可能性が高い",
    r"〜でしょう", r"〜だろう", r"見込", r"想定される",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def flatten_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, list):
        for value in obj:
            out.extend(flatten_strings(value))
    elif isinstance(obj, dict):
        for value in obj.values():
            out.extend(flatten_strings(value))
    return out


def check_required_fields(data: dict[str, Any]) -> tuple[bool, list[str]]:
    missing: list[str] = []

    # --- Case A: topics型（従来） ---
    if "topics" in data and isinstance(data["topics"], list) and len(data["topics"]) > 0:
        for i, topic in enumerate(data["topics"]):
            if not isinstance(topic, dict):
                missing.append(f"topics[{i}](dict)")
                continue
            for key in ("topic", "facts", "unknowns", "next_actions"):
                if key not in topic:
                    missing.append(f"topics[{i}].{key}")
        return len(missing) == 0, missing

    # --- Case B: fallback（会議全体の構造化） ---
    required_lists = ["current_issues", "open_questions", "next_actions"]
    for key in required_lists:
        if key not in data or not isinstance(data[key], list):
            missing.append(f"{key}(list)")

    return len(missing) == 0, missing


def metrics(data: dict[str, Any]) -> dict[str, Any]:
    # 推測っぽい表現を雑に検知（あれば「要人手確認」扱い）
    all_text = "\n".join(flatten_strings(data))
    spec_hits: list[str] = []
    for pattern in SPECULATION_PATTERNS:
        if re.search(pattern, all_text):
            spec_hits.append(pattern)

    # --- Case A: topics型（従来） ---
    topics = data.get("topics", [])
    if isinstance(topics, list) and len(topics) > 0:
        n_topics = len(topics)

        nonempty_topic = 0
        has_unknowns = 0
        has_next_actions = 0
        facts_cnt = 0
        unknowns_cnt = 0
        actions_cnt = 0

        for topic in topics:
            if not isinstance(topic, dict):
                continue
            if str(topic.get("topic", "")).strip():
                nonempty_topic += 1
            if is_nonempty_list(topic.get("unknowns")):
                has_unknowns += 1
            if is_nonempty_list(topic.get("next_actions")):
                has_next_actions += 1

            facts_cnt += len([x for x in (topic.get("facts") or []) if str(x).strip()]) if isinstance(topic.get("facts"), list) else 0
            unknowns_cnt += len([x for x in (topic.get("unknowns") or []) if str(x).strip()]) if isinstance(topic.get("unknowns"), list) else 0
            actions_cnt += len([x for x in (topic.get("next_actions") or []) if str(x).strip()]) if isinstance(topic.get("next_actions"), list) else 0

        return {
            "schema_type": "topics",
            "n_topics": n_topics,
            "topic_filled_rate": (nonempty_topic / n_topics) if n_topics else 0.0,
            "topic_has_unknowns_rate": (has_unknowns / n_topics) if n_topics else 0.0,
            "topic_has_next_actions_rate": (has_next_actions / n_topics) if n_topics else 0.0,
            "avg_facts_per_topic": (facts_cnt / n_topics) if n_topics else 0.0,
            "avg_unknowns_per_topic": (unknowns_cnt / n_topics) if n_topics else 0.0,
            "avg_actions_per_topic": (actions_cnt / n_topics) if n_topics else 0.0,
            "speculation_flag": len(spec_hits) > 0,
            "speculation_patterns_hit": spec_hits[:10],
        }

    # --- Case B: fallback（会議全体） ---
    issues = data.get("current_issues", [])
    questions = data.get("open_questions", [])
    actions = data.get("next_actions", [])
    decisions = data.get("decisions", [])

    issues_cnt = len([x for x in issues if str(x).strip()]) if isinstance(issues, list) else 0
    questions_cnt = len([x for x in questions if str(x).strip()]) if isinstance(questions, list) else 0

    actions_cnt = 0
    owner_filled = 0
    due_filled = 0
    if isinstance(actions, list):
        for action in actions:
            if isinstance(action, str):
                if action.strip():
                    actions_cnt += 1
            elif isinstance(action, dict):
                if any(str(action.get(key, "")).strip() for key in ("action", "owner", "due")):
                    actions_cnt += 1
                if str(action.get("owner", "")).strip():
                    owner_filled += 1
                due_text = str(action.get("due", "")).strip()
                if due_text and due_text not in ("不明", "未定", "N/A"):
                    due_filled += 1

    decisions_cnt = len([x for x in decisions if str(x).strip()]) if isinstance(decisions, list) else 0
    due_missing_cnt = actions_cnt - due_filled

    return {
        "schema_type": "global",
        "issues_cnt": issues_cnt,
        "open_questions_cnt": questions_cnt,
        "next_actions_cnt": actions_cnt,
        "decisions_cnt": decisions_cnt,
        "has_open_questions": questions_cnt > 0,
        "has_next_actions": actions_cnt > 0,
        "action_owner_filled_rate": (owner_filled / actions_cnt) if actions_cnt else 0.0,
        "action_due_filled_rate": (due_filled / actions_cnt) if actions_cnt else 0.0,
        "action_due_filled_cnt": due_filled,
        "action_due_missing_cnt": due_missing_cnt,
        "speculation_flag": len(spec_hits) > 0,
        "speculation_patterns_hit": spec_hits[:10],
    }


def to_markdown(name: str, required_ok: bool, missing: list[str], metric_values: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"## Meeting Structuring Eval: `{name}`")
    lines.append("")
    lines.append("### Structural checks")
    lines.append(f"- required_fields_ok: **{required_ok}**")
    if not required_ok:
        lines.append(f"- missing: `{', '.join(missing)}`")
    lines.append("")
    lines.append("### Metrics")
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    for key in [
        "n_topics",
        "topic_filled_rate",
        "topic_has_unknowns_rate",
        "topic_has_next_actions_rate",
        "avg_facts_per_topic",
        "avg_unknowns_per_topic",
        "avg_actions_per_topic",
        "speculation_flag",
    ]:
        lines.append(f"| {key} | {metric_values.get(key)} |")
    if metric_values.get("speculation_flag"):
        lines.append("")
        lines.append("⚠️ speculation_patterns_hit (要人手確認):")
        for pattern in metric_values.get("speculation_patterns_hit", []):
            lines.append(f"- `{pattern}`")
    lines.append("")
    lines.append("### Human checklist (recommended)")
    lines.append("- [ ] 議事録にない事実を“推測で補完”していない")
    lines.append("- [ ] unknowns が妥当（次に聞くべきことになっている）")
    lines.append("- [ ] next_actions が具体（誰が何をするかが想像できる）")
    lines.append("- [ ] 断定表現が過剰でない（必要なら注意書きを付ける）")
    lines.append("")
    return "\n".join(lines)


def evaluate_summary_data(data: dict[str, Any], summary_path: Path) -> dict[str, Any]:
    required_ok, missing = check_required_fields(data)
    metric_values = metrics(data)
    return {
        "file": str(summary_path),
        "required_fields_ok": required_ok,
        "missing": missing,
        "metrics": metric_values,
    }


def run_meeting_structuring_eval(summary_path: Path, out_json: Path, out_md: Path) -> tuple[Path, Path]:
    data = load_json(summary_path)
    eval_obj = evaluate_summary_data(data, summary_path)

    out_json.write_text(json.dumps(eval_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(
        to_markdown(summary_path.stem, eval_obj["required_fields_ok"], eval_obj["missing"], eval_obj["metrics"]),
        encoding="utf-8",
    )
    return out_json, out_md
