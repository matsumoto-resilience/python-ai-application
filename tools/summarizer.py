from __future__ import annotations
import streamlit as st
from utils.gemini import generate
from utils import history as history_utils


STYLES = {
    "箇条書き": "bullet points",
    "段落文": "flowing paragraphs",
    "一文サマリー": "single sentence",
    "見出し付き": "structured with headings",
}

LENGTHS = {
    "超短（1〜2文）": "1-2 sentences",
    "短め（100字程度）": "about 100 characters",
    "標準（200〜300字）": "200-300 characters",
    "詳細（500字程度）": "about 500 characters",
}

FOCUSES = {
    "全体的に": "overall summary",
    "重要ポイントのみ": "key points only",
    "結論・結果": "conclusions and results",
    "アクションアイテム": "action items and next steps",
}


def render():
    st.header("📝 文章要約")
    st.caption("長い文章を素早く要約します。記事・議事録・論文など何でもOK")

    text = st.text_area(
        "要約したいテキスト *",
        placeholder="ここに要約したいテキストを貼り付けてください...",
        height=200,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        style = st.selectbox("出力スタイル", list(STYLES.keys()))
    with col2:
        length = st.selectbox("要約の長さ", list(LENGTHS.keys()))
    with col3:
        focus = st.selectbox("重点項目", list(FOCUSES.keys()))

    if st.button("要約する", type="primary", use_container_width=True):
        if not text:
            st.warning("要約するテキストを入力してください")
            return
        if len(text) > 20000:
            st.warning(f"テキストが長すぎます（{len(text):,}字）。20,000字以内にしてください。")
            return

        char_count = len(text)
        prompt = f"""以下のテキスト（{char_count}字）を要約してください。

【要約条件】
- 出力スタイル: {STYLES[style]}
- 要約の長さ: {LENGTHS[length]}
- 重点項目: {FOCUSES[focus]}
- 必ず日本語で出力してください

【テキスト】
{text}

要約結果のみを出力してください。前置きや説明文は不要です。"""

        try:
            with st.spinner("要約中..."):
                result = generate(prompt)
        except RuntimeError as e:
            st.error(str(e))
            return

        title = f"要約 - {text[:30].strip()}..."
        st.session_state["summarizer_result"] = {
            "content": result,
            "title": title,
            "original_chars": char_count,
        }

    # 生成結果の表示
    saved = st.session_state.get("summarizer_result")
    if saved:
        result = saved["content"]
        original_chars = saved["original_chars"]
        summary_chars = len(result)
        reduction = round((1 - summary_chars / original_chars) * 100) if original_chars > 0 else 0

        st.divider()
        st.subheader("要約結果")

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("元の文字数", f"{original_chars:,}字")
        col_b.metric("要約後", f"{summary_chars:,}字")
        col_c.metric("削減率", f"{reduction}%")

        st.markdown(result)

        col_dl, col_save = st.columns(2)
        with col_dl:
            st.download_button(
                "📄 要約をダウンロード",
                data=result,
                file_name="summary.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_save:
            if st.button("💾 保存", use_container_width=True):
                history_utils.save_entry("文章要約", saved["title"], result)
                st.success("保存しました！")
