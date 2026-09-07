"""feedback ログ蓄積 / RAG のテスト（APIキー不要）。"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import utils.feedback as feedback_mod  # noqa: E402
import utils.rag as rag_mod  # noqa: E402


def _reload_with_logfile(tmp_path, monkeypatch):
    log_file = tmp_path / "feedback.jsonl"
    monkeypatch.setattr(feedback_mod, "_LOG_FILE", log_file)
    importlib.reload(rag_mod)
    monkeypatch.setattr(rag_mod, "load_feedback", feedback_mod.load_feedback)
    return log_file


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    _reload_with_logfile(tmp_path, monkeypatch)
    rec_id = feedback_mod.save_feedback(
        original_output="AIの原文です。",
        user_edited_output="人が直した文です。",
        feedback_score=feedback_mod.ADOPTED,
        keywords="Python, 入門",
    )
    records = feedback_mod.load_feedback()
    assert len(records) == 1
    r = records[0]
    assert r["id"] == rec_id
    assert r["feedback_score"] == 1
    assert r["keywords"] == ["Python", "入門"]
    assert r["edited"] is True
    assert r["diff"]


def test_keywords_parsing_handles_japanese_comma(tmp_path, monkeypatch):
    _reload_with_logfile(tmp_path, monkeypatch)
    feedback_mod.save_feedback("a", "b", feedback_mod.REJECTED, keywords="猫、犬、鳥")
    assert feedback_mod.load_feedback()[0]["keywords"] == ["猫", "犬", "鳥"]


def test_stats_counts(tmp_path, monkeypatch):
    _reload_with_logfile(tmp_path, monkeypatch)
    feedback_mod.save_feedback("x", "y", feedback_mod.ADOPTED, keywords="a")
    feedback_mod.save_feedback("x", "x", feedback_mod.REJECTED, keywords="a")
    s = feedback_mod.stats()
    assert s == {"total": 2, "adopted": 1, "rejected": 1, "edited": 1}


def test_rag_finds_keyword_match(tmp_path, monkeypatch):
    _reload_with_logfile(tmp_path, monkeypatch)
    feedback_mod.save_feedback(
        "Pythonの原文", "Pythonの採用文", feedback_mod.ADOPTED, keywords="Python, 入門"
    )
    feedback_mod.save_feedback(
        "料理の原文", "料理の採用文", feedback_mod.ADOPTED, keywords="料理, レシピ"
    )
    examples = rag_mod.find_examples(theme="Python 入門ガイド", keywords="Python", limit=1)
    assert len(examples) == 1
    assert "Python" in examples[0]["user_edited_output"]


def test_rag_block_empty_when_no_logs(tmp_path, monkeypatch):
    _reload_with_logfile(tmp_path, monkeypatch)
    assert rag_mod.fewshot_for("なにか", "キーワード") == ""


def test_rag_ignores_rejected(tmp_path, monkeypatch):
    _reload_with_logfile(tmp_path, monkeypatch)
    feedback_mod.save_feedback(
        "原文", "編集文", feedback_mod.REJECTED, keywords="Python"
    )
    assert rag_mod.find_examples(theme="Python", keywords="Python") == []
