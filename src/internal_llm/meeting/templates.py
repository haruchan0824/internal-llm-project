"""Prompt templates for meeting structuring."""

SYSTEM_PROMPT = """あなたは社内の営業支援アシスタントです。
目的は、議事録から提案に必要な事実を構造化して整理することです。
"""

# 推測禁止 + JSON強制（ここが事故を減らす）
USER_PROMPT_TEMPLATE = """以下は顧客との打ち合わせ議事録です。
内容をもとに、営業提案に必要な情報を「推測せず」整理してください。

【重要ルール】
- 議事録に明記されていない情報は推測しない
- 不明な項目は必ず "不明" と書く
- 事実と意見・仮説を分ける
- 出力は JSON のみ（前後に説明文を付けない）

【出力JSONスキーマ】
{{
  "meeting_title": "不明でも可",
  "meeting_date": "不明でも可",
  "participants": ["不明でも可"],
  "customer_profile": {{
    "company": "不明",
    "industry": "不明",
    "department": "不明",
    "role": "不明"
  }},
  "current_issues": ["..."],
  "requirements": ["..."],
  "constraints": {{
    "budget": "不明",
    "schedule": "不明",
    "technical": ["..."]
  }},
  "decisions": ["..."],
  "open_questions": ["..."],
  "next_actions": [
    {{
      "owner": "不明",
      "action": "...",
      "due": "不明"
    }}
  ],
  "proposal_directions": ["..."],
  "evidence_quotes": [
    {{
      "quote": "議事録からの短い抜粋（長くしない）",
      "reason": "この抜粋が何の根拠か"
    }}
  ]
}}

【議事録】
{meeting_text}
"""
