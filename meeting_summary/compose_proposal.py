# meeting_summary/compose_proposal.py
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = """あなたは社内の営業支援アシスタントです。
あなたの役割は、提供された社内資料抜粋（技術資料）に基づいて、営業提案の「根拠」を整理することです。

重要:
- 社内資料に書かれていないことは、絶対に断言しない
- 推測・一般常識で補完しない（一般論も最小限）
- 各主張には必ず出典（文書名・ページ範囲）を付ける
- 断定が難しい場合は「資料上は〜と記載」など、出典ベースの表現にする
"""

USER_PROMPT_TEMPLATE = """以下は、議事録から抽出された「提案方向性」と、それを裏付けるために技術資料から取得した抜粋です。
この抜粋のみを根拠として、営業提案のサマリ（下書き）を作成してください。

【出力ルール】
- 出力は Markdown
- セクション構成は固定:
  1. 提案の要点（1〜3行）
  2. 技術的根拠（箇条書き。各行に出典）
  3. 注意点・適用条件（資料にある範囲のみ。各行に出典）
  4. 次に確認すべき事項（議事録/抜粋から不足が分かる項目。推測しない）
- 「技術的根拠」「注意点」は必ず出典を併記:
  例: （STKネットの基礎知識.pdf p.3-3）

【提案方向性】
{proposal_point}

【技術資料抜粋（evidences）】
{evidence_block}
"""


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def format_evidence_block(evidences: List[Dict[str, Any]], *, max_items: int, max_chars_each: int) -> str:
    lines: List[str] = []
    for i, ev in enumerate(evidences[:max_items], start=1):
        src = ev.get("source", "UNKNOWN")
        ps = ev.get("page_start", "UNKNOWN")
        pe = ev.get("page_end", "UNKNOWN")
        heading = ev.get("heading", "UNKNOWN")
        excerpt = (ev.get("excerpt") or "").strip().replace("\n", " ")
        excerpt = excerpt[:max_chars_each]

        lines.append(
            f"[{i}] source={src}, pages={ps}-{pe}, heading={heading}\n"
            f"excerpt: {excerpt}\n"
        )
    return "\n".join(lines)


def call_llm(*, model: str, prompt: str, temperature: float = 0.2) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="connect_proposal_to_rag.py の出力JSON（*.proposal_support.json）")
    parser.add_argument("--out_dir", default="outputs", help="出力先ディレクトリ")
    parser.add_argument("--max_evidences", type=int, default=5, help="1提案あたりLLMに渡す根拠数")
    parser.add_argument("--max_chars_each", type=int, default=450, help="根拠抜粋の最大文字数")
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY が未設定です。.env を確認してください。")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"input not found: {in_path}")

    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)

    data = load_json(in_path)
    items: List[Dict[str, Any]] = data.get("items") or []
    if not items:
        raise ValueError("入力JSONに items がありません（空です）")

    results: Dict[str, Any] = {
        "source_file": str(in_path),
        "model": model,
        "temperature": args.temperature,
        "outputs": [],
    }

    for idx, item in enumerate(items, start=1):
        proposal_point = item.get("proposal_point", "")
        evidences = item.get("evidences") or []
        if not proposal_point:
            continue

        evidence_block = format_evidence_block(
            evidences,
            max_items=args.max_evidences,
            max_chars_each=args.max_chars_each,
        )

        prompt = USER_PROMPT_TEMPLATE.format(
            proposal_point=proposal_point,
            evidence_block=evidence_block,
        )

        md = call_llm(model=model, prompt=prompt, temperature=args.temperature)

        results["outputs"].append(
            {
                "proposal_point": proposal_point,
                "markdown": md,
                "used_evidences": evidences[: args.max_evidences],
            }
        )

        print(f"[{idx}/{len(items)}] OK: composed for proposal_point='{proposal_point[:30]}'")

    out_path = out_dir / f"{in_path.stem}.composed.md.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK:", out_path)

    # ついでに人間が読みやすい .md も吐く（ポートフォリオで見せやすい）
    md_lines: List[str] = []
    for o in results["outputs"]:
        md_lines.append(f"# 提案方向性\n\n{o['proposal_point']}\n")
        md_lines.append(o["markdown"])
        md_lines.append("\n\n---\n")
    md_out_path = out_dir / f"{in_path.stem}.composed.md"
    md_out_path.write_text("\n".join(md_lines), encoding="utf-8")
    print("OK:", md_out_path)


if __name__ == "__main__":
    main()
