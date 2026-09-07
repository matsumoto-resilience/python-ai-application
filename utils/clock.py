"""タイムスタンプは常に日本時間（JST）で記録する。

Streamlit Community Cloud のサーバーは UTC で動くため、
`datetime.now()` をそのまま使うと 9 時間ずれる。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9), "JST")


def now_iso() -> str:
    """JST の ISO 8601 文字列（秒精度）。例: 2026-09-07T16:14:23+09:00"""
    return datetime.now(JST).isoformat(timespec="seconds")
