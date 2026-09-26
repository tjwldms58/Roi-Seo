"""빈 칸, 공백, NaN, 자리표시 문자를 '없음'으로 봅니다. 0은 값이 있는 것입니다."""

from __future__ import annotations

import math
from datetime import date, datetime, time

DEFAULT_TOKENS = {"", "nan", "none", "null", "n/a", "na", "-", "—", "없음", "해당없음", "해당 없음"}


def is_empty(value, tokens: set[str] | None = None) -> bool:
    words = tokens if tokens is not None else DEFAULT_TOKENS
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str):
        text = value.replace("\u00a0", " ").replace("\u3000", " ").strip()
        if text == "" or text.casefold() in words:
            return True
        return False
    return False


def as_text(value) -> str:
    if is_empty(value):
        return ""
    if isinstance(value, datetime):
        if value.hour or value.minute or value.second:
            return value.strftime("%Y-%m-%d %H:%M")
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return str(value).strip()
