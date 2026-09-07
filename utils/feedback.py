from __future__ import annotations

import difflib
import json
import uuid
from pathlib import Path

from utils.clock import now_iso

_LOG_FILE = Path(__file__).parent.parent / "logs" / "feedback.jsonl"

# feedback_score
ADOPTED = 1
REJECTED = -1


def _parse_keywords(keywords) -> list[str]:
    if keywords is None:
        return []
    if isinstance(keywords, str):
        return [k.strip() for k in keywords.replace("、", ",").split(",") if k.strip()]
    return [str(k).strip() for k in keywords if str(k).strip()]


def make_diff(original: str, edited: str) -> str:
    """人が読める unified diff（変更がなければ空文字）。"""
    if original == edited:
        return ""
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            edited.splitlines(keepends=True),
            fromfile="original_output",
            tofile="user_edited_output",
            n=1,
        )
    )


def save_feedback(
    original_output: str,
    user_edited_output: str,
    feedback_score: int,
    keywords=None,
    meta: dict | None = None,
) -> str:
    """編集差分 / 採否フィードバックを logs/feedback.jsonl に追記する。"""
    record = {
        "id": uuid.uuid4().hex,
        "timestamp": now_iso(),
        "original_output": original_output,
        "user_edited_output": user_edited_output,
        "feedback_score": int(feedback_score),
        "keywords": _parse_keywords(keywords),
        "diff": make_diff(original_output, user_edited_output),
        "edited": original_output != user_edited_output,
    }
    if meta:
        record["meta"] = meta

    _LOG_FILE.parent.mkdir(exist_ok=True)
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record["id"]


def load_feedback() -> list[dict]:
    if not _LOG_FILE.exists():
        return []
    records = []
    for line in _LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def stats() -> dict:
    records = load_feedback()
    adopted = sum(1 for r in records if r.get("feedback_score", 0) > 0)
    rejected = sum(1 for r in records if r.get("feedback_score", 0) < 0)
    edited = sum(1 for r in records if r.get("edited"))
    return {"total": len(records), "adopted": adopted, "rejected": rejected, "edited": edited}
