# AI ライティングツール

Streamlit + Gemini API の日本語ライティング支援ツール。ブログ記事作成・メール返信・要約・校正・SNS投稿・タイトル生成に対応。

ブログ記事作成は **Planner → Writer → Polisher の3段階生成 + ガードレール（AI感の自動判定・再校正）+ 学習ログ（Few-Shot RAG）** で「AIっぽさ」を抑える。

## ローカルで動かす

```bash
pip install -r requirements.txt
```

API キーを次のいずれかで設定：

- `.env` ファイルに `GEMINI_API_KEY=...`
- `.streamlit/secrets.toml`（`.streamlit/secrets.toml.example` をコピー）
- 起動後にサイドバーから直接入力

```bash
python3 -m streamlit run app.py
```

キーは [Google AI Studio](https://aistudio.google.com/app/apikey) から無料で取得できます。

## Streamlit Community Cloud にデプロイ

1. このリポジトリを GitHub に push
2. <https://share.streamlit.io> で GitHub 連携 → リポジトリと `app.py` を指定
3. **Advanced settings** で Python 3.11 を選択
4. **Secrets** に以下を貼り付け（`.streamlit/secrets.toml.example` 参照）：

   ```toml
   GEMINI_API_KEY = "AIza..."
   # APP_PASSWORD = "..."   # 設定するとパスワード認証が有効になる
   ```

5. Deploy

### 注意点

| 項目 | 内容 |
|---|---|
| **保存データ** | Streamlit Cloud のファイルは再起動で初期化される。`logs/`（フィードバック・生成スコア）と `data/history.json`（保存記事）は**永続しない**。永続化するには外部ストレージ（Supabase 等）への差し替えが必要。 |
| **認証** | `APP_PASSWORD` 未設定だと公開 URL は誰でも利用可 → Gemini クォータを消費される。パスワード設定、または Streamlit Cloud の閲覧者制限（メール指定）を推奨。 |
| **キー** | `.env` / `.streamlit/secrets.toml` は `.gitignore` 済み。GitHub に上げないこと。 |

## テスト

```bash
python3 -m pytest          # ガードレール判定・ログ蓄積のテスト（API キー不要）
```

## 構成

- `app.py` — サイドバー（キー初期化・ツール選択・パスワード）+ 各ツールへの委譲
- `tools/` — 各ツールの `render()`
- `utils/` — `gemini`（クライアント）, `pipeline`（3段階生成）, `guardrail`（AI感判定）, `feedback` / `metrics`（学習ログ）, `rag`（Few-Shot）, `ui`（テーマ CSS）
- `design/` — 見た目の元になったデザインキャンバス（`*.dc.html`, `canvas.json`）

詳細は `CLAUDE.md`。
