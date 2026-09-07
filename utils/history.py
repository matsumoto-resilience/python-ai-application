from __future__ import annotations
import json
import uuid
from pathlib import Path

from utils.clock import now_iso

_HISTORY_FILE = Path(__file__).parent.parent / "data" / "history.json"


def load() -> list[dict]:
    if not _HISTORY_FILE.exists():
        return []
    try:
        return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_entry(tool: str, title: str, content: str) -> None:
    entries = load()
    entries.insert(0, {
        "id": uuid.uuid4().hex[:8],
        "tool": tool,
        "title": title,
        "content": content,
        "created_at": now_iso(),
    })
    _HISTORY_FILE.parent.mkdir(exist_ok=True)
    _HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def delete_entry(entry_id: str) -> None:
    entries = [e for e in load() if e["id"] != entry_id]
    _HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
