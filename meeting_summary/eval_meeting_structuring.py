# meeting_summary/eval_meeting_structuring.py
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ざっくり「推測っぽい表現」検知（完全ではないが安全側に倒す）
SPECULATION_PATTERNS = [
    r"と思われる", r"と考えられる", r"推測", r"おそらく", r"可能性が高い",
    r"〜でしょう", r"〜だろう", r"見込", r"想定される",
]

def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def is_nonempty_list(x: Any) -> bool:
    return isinstance(x, list) and any(str(i).strip() for i in x)

def flatten_strings(obj: Any) -> List[str]:
    out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, list):
        for v in obj:
            out.extend(flatten_strings(v))
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(flatten_strings(v))
    return out

def check_required_fields(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    missing: List[str] = []

    # --- Case A: topics型（従来） ---
    if "topics" in data and isinstance(data["topics"], list) and len(data["topics"]) > 0:
        for i, t in enumerate(data["topics"]):
            if not isinstance(t, dict):
                missing.append(f"topics[{i}](dict)")
                continue
            for k in ("topic", "facts", "unknowns", "next_actions"):
                if k not in t:
                    missing.append(f"topics[{i}].{k}")
        ok = len(missing) == 0
        return ok, missing

    # --- Case B: fallback（会議全体の構造化） ---
    # real_02.summary.json のようなスキーマ向け
    required_lists = ["current_issues", "open_questions", "next_actions"]
    for k in required_lists:
        if k not in data or not isinstance(data[k], list):
            missing.append(f"{k}(list)")

    ok = len(missing) == 0
    return ok, missing


def metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    # 推測っぽい表現を雑に検知（あれば「要人手確認」扱い）
    all_text = "\n".join(flatten_strings(data))
    spec_hits = []
    for p in SPECULATION_PATTERNS:
        if re.search(p, all_text):
            spec_hits.append(p)

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

        for t in topics:
            if not isinstance(t, dict):
                continue
            if str(t.get("topic", "")).strip():
                nonempty_topic += 1
            if is_nonempty_list(t.get("unknowns")):
                has_unknowns += 1
            if is_nonempty_list(t.get("next_actions")):
                has_next_actions += 1

            facts_cnt += len([x for x in (t.get("facts") or []) if str(x).strip()]) if isinstance(t.get("facts"), list) else 0
            unknowns_cnt += len([x for x in (t.get("unknowns") or []) if str(x).strip()]) if isinstance(t.get("unknowns"), list) else 0
            actions_cnt += len([x for x in (t.get("next_actions") or []) if str(x).strip()]) if isinstance(t.get("next_actions"), list) else 0

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
    # 期待：current_issues / open_questions / next_actions がlist
    issues = data.get("current_issues", [])
    questions = data.get("open_questions", [])
    actions = data.get("next_actions", [])
    decisions = data.get("decisions", [])

    issues_cnt = len([x for x in issues if str(x).strip()]) if isinstance(issues, list) else 0
    questions_cnt = len([x for x in questions if str(x).strip()]) if isinstance(questions, list) else 0

    # next_actions は dict の場合もあるので柔軟にカウント
    actions_cnt = 0
    owner_filled = 0
    due_filled = 0
    if isinstance(actions, list):
        for a in actions:
            if isinstance(a, str):
                if a.strip():
                    actions_cnt += 1
            elif isinstance(a, dict):
                # action/owner/due のどれかがあれば1件
                if any(str(a.get(k, "")).strip() for k in ("action", "owner", "due")):
                    actions_cnt += 1
                if str(a.get("owner", "")).strip():
                    owner_filled += 1
                if str(a.get("due", "")).strip() and str(a.get("due", "")).strip() not in ("不明", "未定", "N/A"):
                    due_filled += 1

    decisions_cnt = len([x for x in decisions if str(x).strip()]) if isinstance(decisions, list) else 0

    due_missing_cnt = actions_cnt - due_filled  # dueが明示されないアクション数

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

def to_markdown(name: str, required_ok: bool, missing: List[str], m: Dict[str, Any]) -> str:
    lines = []
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
    for k in [
        "n_topics",
        "topic_filled_rate",
        "topic_has_unknowns_rate",
        "topic_has_next_actions_rate",
        "avg_facts_per_topic",
        "avg_unknowns_per_topic",
        "avg_actions_per_topic",
        "speculation_flag",
    ]:
        v = m.get(k)
        lines.append(f"| {k} | {v} |")
    if m.get("speculation_flag"):
        lines.append("")
        lines.append("⚠️ speculation_patterns_hit (要人手確認):")
        for p in m.get("speculation_patterns_hit", []):
            lines.append(f"- `{p}`")
    lines.append("")
    lines.append("### Human checklist (recommended)")
    lines.append("- [ ] 議事録にない事実を“推測で補完”していない")
    lines.append("- [ ] unknowns が妥当（次に聞くべきことになっている）")
    lines.append("- [ ] next_actions が具体（誰が何をするかが想像できる）")
    lines.append("- [ ] 断定表現が過剰でない（必要なら注意書きを付ける）")
    lines.append("")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True, help="outputs/*.summary.json")
    ap.add_argument("--out_json", default=None)
    ap.add_argument("--out_md", default=None)
    args = ap.parse_args()

    summary_path = Path(args.summary)
    data = load_json(summary_path)

    required_ok, missing = check_required_fields(data)
    m = metrics(data)

    eval_obj = {
        "file": str(summary_path),
        "required_fields_ok": required_ok,
        "missing": missing,
        "metrics": m,
    }

    out_json = Path(args.out_json) if args.out_json else summary_path.with_suffix(".eval.json")
    out_md = Path(args.out_md) if args.out_md else summary_path.with_suffix(".eval.md")

    out_json.write_text(json.dumps(eval_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(to_markdown(summary_path.stem, required_ok, missing, m), encoding="utf-8")

    print(f"OK: {out_json}")
    print(f"OK: {out_md}")

if __name__ == "__main__":
    main()
