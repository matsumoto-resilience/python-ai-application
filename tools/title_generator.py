from __future__ import annotations
import streamlit as st
from utils.gemini import generate
from utils import history as history_utils


CONTENT_TYPES = {
    "ブログ記事": "blog article",
    "YouTube動画": "YouTube video",
    "SNS投稿": "social media post",
    "プレゼン資料": "presentation",
    "メルマガ": "email newsletter",
    "本・電子書籍": "book or e-book",
    "ウェビナー": "webinar",
}

STYLES = {
    "クリックしたくなる（バズ系）": "clickbait-style, curiosity-driven",
    "SEO重視": "SEO optimized with keywords",
    "ハウツー・教育系": "how-to, educational",
    "数字を使う": "includes numbers (e.g. 5 ways to...)",
    "問いかけ型": "question format",
    "感情に訴える": "emotionally compelling",
}


def render():
    st.header(":material/title: タイトル・見出し生成")
    st.caption("コンテンツのテーマから複数のタイトル案を一気に生成します")

    topic = st.text_area(
        "コンテンツのテーマ・内容 *",
        placeholder="例: 初心者がPythonを学ぶ際の効率的な勉強方法について",
        height=100,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        content_type = st.selectbox("コンテンツ種別", list(CONTENT_TYPES.keys()))
    with col2:
        style = st.selectbox("タイトルスタイル", list(STYLES.keys()))
    with col3:
        count = st.slider("生成数", min_value=5, max_value=20, value=10)

    keywords = st.text_input("含めたいキーワード（任意）", placeholder="例: Python, 初心者, 独学")
    target = st.text_input("ターゲット読者（任意）", placeholder="例: プログラミング未経験の20〜30代")

    if st.button("タイトルを生成", type="primary", use_container_width=True):
        if not topic:
            st.warning("コンテンツのテーマ・内容を入力してください")
            return
        if len(topic) > 1000:
            st.warning(f"テーマ・内容が長すぎます（{len(topic):,}字）。1,000字以内にしてください。")
            return

        kw_text = f"\n必須キーワード: {keywords}" if keywords else ""
        target_text = f"\nターゲット: {target}" if target else ""

        prompt = f"""あなたはコピーライターのプロです。以下の条件で魅力的なタイトル案を{count}個生成してください。

【コンテンツ情報】
テーマ: {topic}
種別: {CONTENT_TYPES[content_type]}
スタイル: {STYLES[style]}{kw_text}{target_text}

【ルール】
- すべて日本語で
- 各タイトルは1行で完結
- 番号付きリストで出力（1. 2. 3. ...）
- 多様なアプローチで{count}個生成
- タイトルのみ出力（説明文不要）"""

        try:
            with st.spinner("タイトルを生成中..."):
                result = generate(prompt)
        except RuntimeError as e:
            st.error(str(e))
            return

        title = f"タイトル案 - {topic[:30].strip()}..."
        st.session_state["title_generator_result"] = {"content": result, "title": title}

    # 生成結果の表示
    saved = st.session_state.get("title_generator_result")
    if saved:
        result = saved["content"]
        st.divider()
        st.subheader(f"生成されたタイトル案（{count}件）")
        st.markdown(result)

        col_dl, col_save = st.columns(2)
        with col_dl:
            st.download_button(
                "📄 タイトル案をダウンロード",
                data=result,
                file_name="title_ideas.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_save:
            if st.button("保存", icon=":material/save:", use_container_width=True):
                history_utils.save_entry("タイトル・見出し生成", saved["title"], result)
                st.success("保存しました！")
