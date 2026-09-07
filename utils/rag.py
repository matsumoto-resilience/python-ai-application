from __future__ import annotations

import re

from utils.feedback import load_feedback

_TOKEN = re.compile(r"[0-9A-Za-z_]+|[ぁ-んァ-ヶ一-龠]+")

# Few-Shot に載せる1例あたりの最大文字数
_SNIPPET_LEN = 400


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text or "") if len(t) >= 2}


def _score(query_tokens: set[str], record: dict) -> float:
    kw = record.get("keywords") or []
    rec_tokens = _tokens(" ".join(kw))
    rec_tokens |= _tokens(record.get("user_edited_output", "")[:200])

    if not query_tokens or not rec_tokens:
        return 0.0

    overlap = len(query_tokens & rec_tokens)
    # キーワード完全一致を重めに評価
    kw_hit = len(query_tokens & {k.lower() for k in kw})
    return overlap + kw_hit * 2.0


def find_examples(theme: str = "", keywords="", limit: int = 3) -> list[dict]:
    """採用（feedback_score > 0）かつ編集済みの過去ログから、類似する例を返す。"""
    if isinstance(keywords, (list, tuple, set)):
        keywords = ", ".join(str(k) for k in keywords)
    query_tokens = _tokens(f"{theme} {keywords}")

    candidates = [
        r
        for r in load_feedback()
        if r.get("feedback_score", 0) > 0
        and r.get("user_edited_output")
        and r.get("edited")
    ]

    scored = [(_score(query_tokens, r), r) for r in candidates]
    scored = [(s, r) for s, r in scored if s > 0]
    scored.sort(key=lambda x: (x[0], x[1].get("timestamp", "")), reverse=True)

    # 類似が全く無ければ、新しい採用例をフォールバックで使う
    if not scored:
        fallback = sorted(candidates, key=lambda r: r.get("timestamp", ""), reverse=True)
        return fallback[:limit]

    return [r for _, r in scored[:limit]]


def _trim(text: str) -> str:
    text = text.strip()
    return text if len(text) <= _SNIPPET_LEN else text[:_SNIPPET_LEN] + " …(以下略)"


def build_fewshot_block(examples: list[dict]) -> str:
    """Polisher プロンプトに差し込む Few-Shot ブロックを組み立てる。"""
    if not examples:
        return ""

    parts = [
        "【お手本：過去に読者から好まれた修正例】",
        "以下は「AIが生成した原文」と「人が直して採用された文」の対です。",
        "同じような方向性（言い回し・リズム・語りかけ方）を参考にしてください。",
    ]
    for i, ex in enumerate(examples, 1):
        parts.append(
            f"\n― 例{i} ―\n"
            f"[修正前]\n{_trim(ex.get('original_output', ''))}\n\n"
            f"[修正後（採用）]\n{_trim(ex.get('user_edited_output', ''))}"
        )
    return "\n".join(parts)


def fewshot_for(theme: str = "", keywords="", limit: int = 3) -> str:
    return build_fewshot_block(find_examples(theme, keywords, limit))
