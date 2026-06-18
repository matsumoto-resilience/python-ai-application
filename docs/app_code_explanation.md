# Streamlit × Gemini APIで作るAIライティングツール ── コード徹底解説

---

## はじめに

このコードは、Google の AI「Gemini」を使ったライティングツールのメインファイル（`app.py`）です。Streamlit というライブラリを使って、Pythonだけでウェブアプリを作っています。

---

## ① ライブラリの読み込み

```python
import os
import streamlit as st
from dotenv import load_dotenv

from utils import gemini as gemini_utils
from tools import blog_writer, email_reply, summarizer, ...
```

| ライブラリ | 役割 |
|---|---|
| `os` | 環境変数（APIキーなど）を読み取る |
| `streamlit` | ウェブ画面のUI（ボタン・テキストなど）を作る |
| `dotenv` | `.env` ファイルから設定を読み込む |
| `gemini_utils` | 自作モジュール。Gemini APIへの接続を担当 |
| `blog_writer` 等 | 各ツールの画面ロジック |

---

## ② アプリの基本設定

```python
load_dotenv()

st.set_page_config(
    page_title="AI ライティングツール",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

`load_dotenv()` はアプリ起動時に `.env` ファイルを読み込みます。`GEMINI_API_KEY=AIza...` のような設定がここで読み込まれます。

`st.set_page_config()` はブラウザのタブに表示されるタイトルやアイコン、レイアウトを設定します。これは**必ずStreamlitの最初に呼ぶ**必要があります。

---

## ③ ツール一覧の定義

```python
TOOLS = {
    "✍️ ブログ記事作成": blog_writer.render,
    "📧 メール返信作成": email_reply.render,
    "📝 文章要約": summarizer.render,
    ...
}
```

辞書（dict）のキーが「ツール名」、値が「そのツールを表示する関数」です。

後でサイドバーの選択結果に応じて `TOOLS[selected_tool]()` と呼び出すだけで、選ばれたツールの画面が表示される仕組みです。新しいツールを追加したいときも、ここに1行足すだけで済みます。

---

## ④ サイドバーの構築

```python
with st.sidebar:
    ...
```

`with st.sidebar:` のブロック内に書いたUI部品は、すべて**左のサイドバー**に表示されます。

### APIキーの取得

```python
api_key_env = os.getenv("GEMINI_API_KEY", "")
if api_key_env:
    api_key = api_key_env
    st.success("API キー: 環境変数から読み込み済み", icon="✅")
else:
    api_key = st.text_input("Gemini API キー", type="password", ...)
```

まず `.env` ファイルにキーがあるか確認し、あればそれを使います。なければサイドバーにパスワード入力欄を表示してユーザーに手入力してもらいます。

### モデルの初期化と一覧取得

```python
if api_key:
    gemini_utils.init_model(api_key=api_key, model_name="gemini-2.5-flash")
    available_models = gemini_utils.list_available_models()
```

APIキーが確定したタイミングで Gemini に接続し、そのキーで**実際に使えるモデルの一覧**を取得します。これを次の `st.selectbox()` に渡すことで、存在しないモデル名を選んでしまうエラーを防いでいます。

### モデル選択 → 再初期化

```python
model_name = st.selectbox("使用モデル", available_models, ...)

if api_key and model_name:
    gemini_utils.init_model(api_key=api_key, model_name=model_name)
```

ユーザーがセレクトボックスでモデルを選んだら、そのモデルで**もう一度初期化**します。これでクォータ超過時に別モデルへ切り替えられます。

---

## ⑤ メインエリアの表示制御

```python
if not api_key:
    st.info("👈 サイドバーから Gemini API キーを入力してください...")
    st.stop()
```

`st.stop()` はそれ以降のコードを**実行しない**命令です。APIキーがない状態でツールを呼び出すとエラーになるため、ここで処理を止めています。

```python
TOOLS[selected_tool]()
```

最後の1行がすべてです。サイドバーで選ばれたツール名をキーに辞書を引き、対応する `render()` 関数を呼び出します。

---

## 全体の流れまとめ

```
アプリ起動
  ↓
.env 読み込み（APIキー取得）
  ↓
サイドバー描画
  ├─ APIキー確認・入力
  ├─ 使えるモデル一覧を取得 → セレクトボックス表示
  └─ ツール選択（ラジオボタン）
  ↓
APIキーなし → 案内メッセージを出して停止
  ↓
選ばれたツールの render() を実行 → メインエリアに表示
```

この設計のポイントは「**ツールを追加するときに `app.py` への変更が最小限で済む**」点です。新しいツールファイルを作って `TOOLS` 辞書に登録するだけで、ナビゲーションも画面切り替えも自動的に動きます。
