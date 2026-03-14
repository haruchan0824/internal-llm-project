"""Backward-compatible masking helper exports."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from internal_llm.meeting.mask import MASK_RULES, mask_text

__all__ = ["MASK_RULES", "mask_text"]
