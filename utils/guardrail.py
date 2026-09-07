from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from utils.gemini import generate

# --- ルールベース判定の設定 --------------------------------------------------

# 常套句（AI感の強い定型表現）
NG_PHRASES = {
    "〜と言えるでしょう": re.compile(r"と言える(でしょう|だろう)"),
    "〜について解説します": re.compile(r"について(解説|説明)します"),
    "いかがでしたでしょうか": re.compile(r"いかが(でした|でし)たか|いかがでしたでしょうか"),
}

# この回数以上の使用で「連続・多用」とみなす
NG_PHRASE_LIMIT = 2

# 1文の許容文字数
MAX_SENTENCE_LEN = 100

# 具体例・体験談を示唆する手がかり
CONCRETE_HINTS = re.compile(
    r"例えば|たとえば|具体的には|実際に|私(は|が|の)|僕(は|が|の)|当時|ある日|"
    r"\d+\s*(円|万円|%|％|時間|分|日|kg|キロ|人|回|歳|年)"
)

_SENTENCE_END = re.compile(r"[。！？!?]")
_MD_MARKUP = re.compile(r"^\s*(#+\s|[-*]\s|\d+\.\s|\|)")


@dataclass
class GuardrailReport:
    passed: bool
    score: int  # 0-100
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def feedback_text(self) -> str:
        lines = list(self.violations) + list(self.warnings)
        return "\n".join(f"- {x}" for x in lines) if lines else "特になし"


def _split_sentences(text: str) -> list[str]:
    """見出し・箇条書き行を除いた本文を文単位に分割する。"""
    body_lines = [ln for ln in text.splitlines() if ln.strip() and not _MD_MARKUP.match(ln)]
    body = "".join(body_lines)
    parts = _SENTENCE_END.split(body)
    return [p.strip() for p in parts if p.strip()]


def _paragraphs(text: str) -> list[str]:
    blocks, buf = [], []
    for ln in text.splitlines():
        if _MD_MARKUP.match(ln):
            continue
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            blocks.append(" ".join(buf))
            buf = []
    if buf:
        blocks.append(" ".join(buf))
    return blocks


def check_rules(text: str) -> GuardrailReport:
    violations: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    # 1. 常套句の多用
    phrase_counts = {}
    for label, pat in NG_PHRASES.items():
        n = len(pat.findall(text))
        phrase_counts[label] = n
        if n >= NG_PHRASE_LIMIT:
            violations.append(f"常套句「{label}」を{n}回使用（{NG_PHRASE_LIMIT}回以上はNG）")
        elif n == 1:
            warnings.append(f"常套句「{label}」を1回使用（できれば言い換える）")
    details["phrase_counts"] = phrase_counts

    # 2. 長すぎる文
    sentences = _split_sentences(text)
    long_sents = [s for s in sentences if len(s) > MAX_SENTENCE_LEN]
    details["long_sentence_count"] = len(long_sents)
    if long_sents:
        sample = long_sents[0][:40]
        violations.append(
            f"100字を超える長文が{len(long_sents)}文（例:「{sample}...」）。短く区切る"
        )

    # 3. 具体例・体験談的描写が最低1箇所
    has_concrete = bool(CONCRETE_HINTS.search(text))
    details["has_concrete_example"] = has_concrete
    if not has_concrete:
        violations.append("具体例・体験談的な描写が見当たらない（最低1箇所必要）")

    # 4. 問いかけ（断定一辺倒の回避）
    question_count = text.count("？") + text.count("?")
    details["question_count"] = question_count
    if question_count == 0:
        warnings.append("読者への問いかけが0回（断定と問いかけを織り交ぜる）")

    # 5. 段落ごとの共感フック（ヒューリスティック）
    paras = _paragraphs(text)
    details["paragraph_count"] = len(paras)
    if len(paras) >= 3 and question_count == 0 and not has_concrete:
        warnings.append("段落ごとの一言まとめ・共感フックが弱い可能性")

    # スコア化（100点満点、違反 -25 / 警告 -8）
    score = max(0, 100 - 25 * len(violations) - 8 * len(warnings))
    passed = len(violations) == 0

    return GuardrailReport(
        passed=passed,
        score=score,
        violations=violations,
        warnings=warnings,
        details=details,
    )


# --- 評価用プロンプトによる判定 --------------------------------------------

_EVAL_PROMPT = """あなたは日本語コンテンツの品質評価者です。
次の記事を評価し、JSONのみを出力してください（前後に文章を付けない）。

評価観点:
- ai_feel: 機械的・定型的でAIっぽくないか（0-100、高いほど人間らしい）
- empathy: 読者への共感・語りかけがあるか（0-100）
- concrete: 具体例・体験談・数字が十分か（0-100）
- issues: 気になった点の短い日本語の配列（最大3個）

出力フォーマット:
{{"ai_feel": <int>, "empathy": <int>, "concrete": <int>, "issues": [<string>, ...]}}

【記事】
{text}
"""


def check_with_prompt(text: str) -> dict:
    """LLM評価。失敗時は空dictを返す（ルール判定のみで続行できるように）。"""
    try:
        raw = generate(_EVAL_PROMPT.format(text=text[:6000]))
    except Exception:
        return {}
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    return data


# --- 統合エントリポイント ------------------------------------------------------

# LLM評価でこの値を下回る観点があれば違反扱い
EVAL_THRESHOLD = 60


def evaluate(text: str, use_llm: bool = True) -> GuardrailReport:
    report = check_rules(text)

    if use_llm:
        llm = check_with_prompt(text)
        if llm:
            report.details["llm"] = llm
            labels = {"ai_feel": "AI感の低さ", "empathy": "共感", "concrete": "具体性"}
            for key, label in labels.items():
                val = llm.get(key)
                if isinstance(val, (int, float)) and val < EVAL_THRESHOLD:
                    report.violations.append(f"LLM評価: {label}スコアが低い（{int(val)}/100）")
            for issue in (llm.get("issues") or [])[:3]:
                if issue:
                    report.warnings.append(f"LLM指摘: {issue}")
            report.score = min(
                report.score,
                int((llm.get("ai_feel", 100) + llm.get("empathy", 100) + llm.get("concrete", 100)) / 3),
            )
            report.passed = len(report.violations) == 0

    return report
