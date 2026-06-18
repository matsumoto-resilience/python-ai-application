# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## アプリの起動

```bash
python3 -m streamlit run app.py
```

Gemini API キーが必要です。`.env` ファイル（`GEMINI_API_KEY=...`）に設定するか、起動後にサイドバーから入力してください。

## アーキテクチャ

シングルページの Streamlit アプリ。`app.py` がサイドバー（API キーの初期化とツール選択）を管理し、各ツールモジュールにレンダリングを委譲します。各ツールは `tools/` 配下の Python ファイルで、Streamlit UI の構築と `utils/gemini.generate()` の呼び出しを行う `render()` 関数を持ちます。

**Gemini クライアント** (`utils/gemini.py`): モジュールレベルのシングルトン。API キーが確定した後、`app.py` 内で `init_model()` を一度呼び出す必要があります。その後、各ツールから `generate()` が使えます。デフォルトモデルは `gemini-2.0-flash`。

## 新しいツールの追加手順

1. `tools/my_tool.py` を作成し、`render()` 関数を実装する
2. `app.py` の `TOOLS` 辞書に登録する

## Python バージョンについて

このプロジェクトは Python 3.9 で動作します。`X | Y` 形式のユニオン型を使うファイルには、先頭に `from __future__ import annotations` を追加してください。
