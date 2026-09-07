"""Polisher/ガードレールのルールベース判定のテスト（APIキー不要）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import guardrail  # noqa: E402

GOOD_ARTICLE = """# 【Python入門】最初の30分でできること

## 【はじめに】
プログラミングを始めたいけれど、何から手をつければいいか分からない。
そんな気持ち、よく分かります。私も最初はエディタを開いたまま10分固まっていました。
この記事を読めば、最初の一歩が見えてきます。

## 【まず環境を作ろう】
たとえば公式サイトからインストーラを落とすだけで、5分あれば準備は終わります。
難しく考えなくて大丈夫。まずは動かしてみませんか。

## 【まとめ】
- 環境構築は5分で終わる
- 小さく動かすことが上達の近道
次は簡単な計算プログラムを書いてみましょう。
"""

AI_ARTICLE = """# Pythonについて

## はじめに
本記事ではPythonについて解説します。

## 本文
Pythonは非常に人気のあるプログラミング言語であり、初心者にも扱いやすく多くの企業で採用されており学習コストが低いため多くの学習者にとって最適な選択肢であり将来性も高く困ることはほとんどないと言えるでしょう。
またPythonはWeb開発やデータ分析など幅広い分野で利用されていると言えるでしょう。

## まとめ
いかがでしたでしょうか。Pythonについて解説しました。
"""


def test_good_article_passes():
    report = guardrail.check_rules(GOOD_ARTICLE)
    assert report.passed
    assert report.score >= 70


def test_ai_article_flags_ng_phrase_overuse():
    report = guardrail.check_rules(AI_ARTICLE)
    assert not report.passed
    joined = " ".join(report.violations)
    assert "と言えるでしょう" in joined


def test_ai_article_flags_long_sentence():
    report = guardrail.check_rules(AI_ARTICLE)
    assert report.details["long_sentence_count"] >= 1
    assert any("100字" in v for v in report.violations)


def test_ai_article_flags_missing_concrete_example():
    report = guardrail.check_rules(AI_ARTICLE)
    assert report.details["has_concrete_example"] is False
    assert any("具体例" in v for v in report.violations)


def test_good_article_has_concrete_example():
    report = guardrail.check_rules(GOOD_ARTICLE)
    assert report.details["has_concrete_example"] is True


def test_ihaga_deshita_detected():
    report = guardrail.check_rules("いかがでしたでしょうか。" * 2)
    assert report.details["phrase_counts"]["いかがでしたでしょうか"] >= 2


def test_feedback_text_is_bulleted():
    report = guardrail.check_rules(AI_ARTICLE)
    text = report.feedback_text()
    assert text.startswith("- ")
