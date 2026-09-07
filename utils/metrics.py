"""生成ごとの品質スコアを記録し、ダッシュボード用に集計する。

- log_generation(): 1回の生成結果を logs/generations.jsonl に追記
- load_generations(): 記録の読み出し
- dashboard_summary(): 保存済み記事・フィードバックと合わせた集計
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from utils import history as history_utils
from utils.feedback import load_feedback

_GEN_LOG = Path(__file__).parent.parent / "logs" / "generations.jsonl"


def log_generation(
    tool: str,
    title: str,
    score: int,
    passed: bool,
    retries: int = 0,
    dims: dict | None = None,
) -> None:
    _GEN_LOG.parent.mkdir(exist_ok=True)
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tool": tool,
        "title": title,
        "score": int(score),
        "passed": bool(passed),
        "retries": int(retries),
        "dims": dims or {},
    }
    with _GEN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_generations() -> list[dict]:
    if not _GEN_LOG.exists():
        return []
    out = []
    for line in _GEN_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def dashboard_summary() -> dict:
    gens = load_generations()
    fb = load_feedback()

    scores = [g["score"] for g in gens if isinstance(g.get("score"), int)]
    avg_score = round(sum(scores) / len(scores)) if scores else None
    pass_rate = (
        round(100 * sum(1 for g in gens if g.get("passed")) / len(gens)) if gens else None
    )

    adopted = [r for r in fb if r.get("feedback_score", 0) > 0]
    rejected = [r for r in fb if r.get("feedback_score", 0) < 0]
    adopted_asis = sum(1 for r in adopted if not r.get("edited"))
    adopted_edited = sum(1 for r in adopted if r.get("edited"))
    decided = len(adopted) + len(rejected)
    adoption_rate = round(100 * len(adopted) / decided) if decided else None

    # ツール別の保存件数（全ツールを横断できる history を使う）
    tool_counts = Counter(e.get("tool", "その他") for e in history_utils.load())

    return {
        "generations": gens,
        "total_generations": len(gens),
        "scores": scores,
        "avg_score": avg_score,
        "pass_rate": pass_rate,
        "feedback_total": len(fb),
        "adopted_asis": adopted_asis,
        "adopted_edited": adopted_edited,
        "rejected": len(rejected),
        "adoption_rate": adoption_rate,
        "tool_counts": dict(tool_counts),
    }
