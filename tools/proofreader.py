from __future__ import annotations
import streamlit as st
from utils.gemini import generate
from utils import history as history_utils


MODES = {
    "誤字・脱字チェック": "Check for typos, missing characters, and basic grammatical errors only",
    "文章改善": "Improve clarity, readability, and flow while keeping the original intent",
    "フォーマル化": "Rewrite in formal, professional Japanese",
    "カジュアル化": "Rewrite in friendly, casual Japanese",
    "簡潔化": "Simplify and condense without losing key meaning",
}


def render():
    st.header("🔍 文章校正・改善")
    st.caption("文章の誤字脱字チェックから、文体の改善まで対応します")

    text = st.text_area(
        "校正・改善したいテキスト *",
        placeholder="ここに校正・改善したいテキストを貼り付けてください...",
        height=200,
    )

    mode = st.selectbox("モード", list(MODES.keys()))
    extra = st.text_input("追加の指示（任意）", placeholder="例: 若い女性向けの文体にしてください", max_chars=200)

    show_diff = st.checkbox("変更箇所をわかりやすく表示する", value=True)

    if st.button("校正・改善する", type="primary", use_container_width=True):
        if not text:
            st.warning("テキストを入力してください")
            return
        if len(text) > 10000:
            st.warning(f"テキストが長すぎます（{len(text):,}字）。10,000字以内にしてください。")
            return

        extra_text = f"\n追加指示: {extra}" if extra else ""
        diff_instruction = (
            "\n変更した箇所を **太字** で強調して示してください。"
            if show_diff
            else ""
        )

        prompt = f"""あなたはプロの日本語編集者です。以下のテキストを指定されたモードで処理してください。

【モード】{MODES[mode]}
{extra_text}
{diff_instruction}

【元のテキスト】
{text}

【出力形式】
## 校正・改善後のテキスト
（改善後の全文をここに出力）

## 変更点のまとめ
（どのような変更を行ったか箇条書きで3〜5点）"""

        try:
            with st.spinner("校正・改善中..."):
                result = generate(prompt)
        except RuntimeError as e:
            st.error(str(e))
            return

        title = f"校正 - {text[:30].strip()}..."
        st.session_state["proofreader_result"] = {"content": result, "title": title}

    # 生成結果の表示
    saved = st.session_state.get("proofreader_result")
    if saved:
        result = saved["content"]
        st.divider()
        st.subheader("結果")
        st.markdown(result)

        col_dl, col_save = st.columns(2)
        with col_dl:
            st.download_button(
                "📄 結果をダウンロード",
                data=result,
                file_name="proofread_result.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_save:
            if st.button("💾 保存", use_container_width=True):
                history_utils.save_entry("文章校正・改善", saved["title"], result)
                st.success("保存しました！")
