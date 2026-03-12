# meeting_summary/mask.py
import re
from typing import Tuple, Dict

# 例：最低限のルール。自社/顧客名が分かるなら追加。
MASK_RULES = [
    # メール
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<EMAIL>"),
    # 電話っぽいもの（雑）
    (r"\b0\d{1,4}-\d{1,4}-\d{4}\b", "<PHONE>"),
    # 「株式会社〇〇」っぽいもの（雑）
    (r"(株式会社|有限会社|合同会社)\s*[一-龥A-Za-z0-9・]+", "<COMPANY>"),
]

def mask_text(text: str) -> Tuple[str, Dict[str, str]]:
    """
    ルールベースでマスク。復元マップは最小実装では使わなくてOK。
    """
    redacted = text
    mapping: Dict[str, str] = {}
    for pattern, token in MASK_RULES:
        redacted = re.sub(pattern, token, redacted)
    return redacted, mapping
