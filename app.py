import os

import streamlit as st
from dotenv import load_dotenv

from utils import gemini as gemini_utils
from utils import ui as ui_utils
from tools import blog_writer, email_reply, summarizer, proofreader, social_post, title_generator, article_history

load_dotenv()

st.set_page_config(
    page_title="AI ライティングツール",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui_utils.inject_global_css()


def _check_password() -> bool:
    """APP_PASSWORD が Secrets に設定されている場合のみ、簡易パスワード認証を行う。

    未設定ならゲートは無効（誰でもアクセス可）。
    """
    expected = os.getenv("APP_PASSWORD", "")
    if not expected:
        try:
            expected = str(st.secrets.get("APP_PASSWORD", "") or "")
        except Exception:
            expected = ""
    if not expected or st.session_state.get("_auth_ok"):
        return True

    st.markdown("### :material/lock: このアプリはパスワードで保護されています")
    with st.form("login"):
        pw = st.text_input("パスワード", type="password")
        if st.form_submit_button("ログイン", type="primary"):
            if pw == expected:
                st.session_state["_auth_ok"] = True
                st.rerun()
            else:
                st.error("パスワードが違います")
    return False


if not _check_password():
    st.stop()

TOOLS = {
    "ブログ記事作成": blog_writer.render,
    "メール返信作成": email_reply.render,
    "文章要約": summarizer.render,
    "文章校正・改善": proofreader.render,
    "SNS投稿文作成": social_post.render,
    "タイトル・見出し生成": title_generator.render,
    "保存済み記事": article_history.render,
}

TOOL_ICONS = {
    "ブログ記事作成": ":material/edit:",
    "メール返信作成": ":material/mail:",
    "文章要約": ":material/notes:",
    "文章校正・改善": ":material/edit_note:",
    "SNS投稿文作成": ":material/tag:",
    "タイトル・見出し生成": ":material/title:",
    "保存済み記事": ":material/bookmark:",
}

# 保存済み記事は API キー不要
NO_API_TOOLS = {"保存済み記事"}

# --- サイドバー ---
with st.sidebar:
    st.title(":material/stylus: AI Writing")
    st.caption("Powered by Gemini")
    st.divider()

    # API キー設定（.env / Streamlit Secrets → なければ手入力）
    api_key_env = gemini_utils.get_api_key()
    if api_key_env:
        api_key = api_key_env
        st.success("API キー: 設定から読み込み済み", icon=":material/check_circle:")
    else:
        api_key = st.text_input(
            "Gemini API キー",
            type="password",
            placeholder="AIza...",
            help=".env ファイルに GEMINI_API_KEY を設定するか、ここに直接入力してください",
        )

    # APIキーがある場合のみモデル選択を表示
    if api_key:
        try:
            # モデル一覧取得のための仮初期化
            gemini_utils.init_model(api_key=api_key, model_name="gemini-2.5-flash")
            available_models = gemini_utils.list_available_models()
            if not api_key_env:
                st.success("API キーを設定しました", icon=":material/check_circle:")
        except Exception:
            st.error("API キーの設定に失敗しました。キーを確認してください。")
            available_models = []

        if available_models:
            model_name = st.selectbox(
                "使用モデル",
                available_models,
                index=available_models.index("gemini-2.5-flash") if "gemini-2.5-flash" in available_models else 0,
                help="クォータ超過時は別モデルに切り替えてください",
            )
            # 選択されたモデルで初期化
            try:
                gemini_utils.init_model(api_key=api_key, model_name=model_name)
            except Exception:
                st.error("モデルの設定に失敗しました。")
        else:
            model_name = None

    st.divider()

    # ツール選択
    st.subheader("ツール選択")
    selected_tool = st.radio(
        "使いたいツールを選択",
        list(TOOLS.keys()),
        format_func=lambda name: f"{TOOL_ICONS.get(name, '')} {name}",
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("入力したテキストは Google Gemini API（外部サービス）に送信されます。個人情報・機密情報の入力はお控えください。")
    st.caption("© 2026 AI Writing Tool")

# --- メインエリア ---
if selected_tool in NO_API_TOOLS:
    TOOLS[selected_tool]()
    st.stop()

if not api_key:
    st.info(
        "サイドバーから Gemini API キーを入力してください。\n\n"
        "[Google AI Studio](https://aistudio.google.com/app/apikey) から無料で取得できます。",
        icon=":material/vpn_key:",
    )
    st.stop()

try:
    gemini_utils.get_model()
except ValueError:
    st.warning("モデルが初期化されていません。サイドバーを確認してください。")
    st.stop()

TOOLS[selected_tool]()
