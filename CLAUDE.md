# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## アプリの起動

```bash
python3 -m streamlit run app.py
```

API キーが必要です（**Gemini または Anthropic Claude**）。`.env`（`GEMINI_API_KEY=...` または `ANTHROPIC_API_KEY=...`）、`.streamlit/secrets.toml`、または起動後にサイドバーから入力。

## アーキテクチャ

シングルページの Streamlit アプリ。`app.py` がサイドバー（API キーの初期化とツール選択）を管理し、各ツールモジュールにレンダリングを委譲します。各ツールは `tools/` 配下の Python ファイルで、Streamlit UI の構築と `utils/gemini.generate()` の呼び出しを行う `render()` 関数を持ちます。

**LLM クライアント** (`utils/gemini.py`): モジュールレベルのシングルトン。**Gemini と Claude の両対応**で、キーの先頭で自動判別（`sk-ant-...` → Anthropic、それ以外 → Gemini）。API キー確定後に `app.py` で `init_model(api_key, model_name)` を一度呼び、各ツールは `generate(prompt)` を呼ぶ（プロバイダは透過）。デフォルトモデルは Gemini=`gemini-2.5-flash` / Claude=`claude-opus-5`。`detect_provider()` / `get_provider()` でプロバイダを判定。

### 記事生成パイプライン（`tools/blog_writer.py`）

ブログ記事作成は単一プロンプトではなく多段階で生成します（`architecture.md` の Task 1〜4）。

- `utils/pipeline.py`: Planner（構成・共感設計）→ Writer（初稿）→ Polisher（脱AI校正）を順に実行する `run_pipeline()`。
- `utils/guardrail.py`: 生成文のAI感をルールベース + 評価用プロンプトで判定（`evaluate()`）。未達なら pipeline が Polisher を再実行（`max_retries`）。
- `utils/feedback.py`: ユーザーの編集差分と採用/ボツを `logs/feedback.jsonl` に追記（`save_feedback()`）。`logs/` は gitignore 済み。
- `utils/rag.py`: 過去の採用ログからテーマ/KW が近い例を検索し、Polisher プロンプトへ Few-Shot として注入（`fewshot_for()`）。

ルールベース判定のテストは `tests/`（`python3 -m pytest`、APIキー不要）。

### 見た目（テーマ）

`ai-writing-redesign.html`（デザインキャンバス）に沿った「白基調 + ブルー + 角丸カード + ソフトシャドウ」。

- `.streamlit/config.toml`: 配色・角丸・フォント（見出し Poppins、本文 Noto Sans JP）
- `utils/ui.py` `inject_global_css()`: フォント読み込み、サイドバーのナビ風スタイル、ボタン・入力・カード等の CSS。`app.py` の先頭で一度呼ぶ。本文コンテナは画面幅に追従（上限 1400px）
- アイコンは絵文字ではなく Material Symbols（`:material/xxx:` / `st.button(icon=...)`）。ツール名の絵文字は `app.py` の `TOOL_ICONS` で管理
- `utils/ui.py` `render_score_panel()`: ガードレールの品質スコアをゲージ + 内訳バー（inline SVG/HTML）で表示

### ダッシュボード（`tools/article_history.py`）

「保存済み記事」の先頭に品質・履歴のグラフを表示（Altair）。

- `utils/metrics.py` `log_generation()`: 生成ごとにスコアを `logs/generations.jsonl` へ追記。`blog_writer` が呼ぶ
- `utils/metrics.py` `dashboard_summary()`: generations / feedback / history を集計
- グラフ: スコア推移（折れ線）・フィードバック内訳（ドーナツ）・ツール別保存数（棒）。多系列の配色は dataviz スキルの検証済みパレット

## 新しいツールの追加手順

1. `tools/my_tool.py` を作成し、`render()` 関数を実装する
2. `app.py` の `TOOLS` 辞書に登録する

## Python バージョンについて

このプロジェクトは Python 3.9 で動作します。`X | Y` 形式のユニオン型を使うファイルには、先頭に `from __future__ import annotations` を追加してください。
