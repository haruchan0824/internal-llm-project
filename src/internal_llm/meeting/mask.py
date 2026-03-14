from __future__ import annotations

import re
from typing import Dict

# 例：最低限のルール。自社/顧客名が分かるなら追加。
MASK_RULES = [
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<EMAIL>"),
    (r"\b0\d{1,4}-\d{1,4}-\d{4}\b", "<PHONE>"),
    (r"(株式会社|有限会社|合同会社)\s*[一-龥A-Za-z0-9・]+", "<COMPANY>"),
]


def mask_text(text: str) -> tuple[str, Dict[str, str]]:
    """Apply lightweight rule-based masking for portfolio-safe preprocessing."""
    redacted = text
    mapping: Dict[str, str] = {}
    for pattern, token in MASK_RULES:
        redacted = re.sub(pattern, token, redacted)
    return redacted, mapping
