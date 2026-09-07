from __future__ import annotations
import streamlit as st
from utils.gemini import generate
from utils import history as history_utils


PLATFORMS = {
    "X (Twitter)": {
        "desc": "140字以内、ハッシュタグ活用、インパクト重視",
        "limit": "140字以内",
    },
    "Instagram": {
        "desc": "絵文字多用、改行でリズム、ハッシュタグ多め",
        "limit": "2200字以内（実用的には300字程度）",
    },
    "LinkedIn": {
        "desc": "ビジネス向け、専門性を示す、読みやすい段落",
        "limit": "3000字以内",
    },
    "Facebook": {
        "desc": "ストーリー性、共感を呼ぶ、リンク添付前提OK",
        "limit": "1500字以内",
    },
    "note": {
        "desc": "読み物として完結、見出し・本文構成、日本語読者向け",
        "limit": "制限なし（500〜1500字程度が適切）",
    },
}

GOALS = {
    "認知拡大": "awareness and reach",
    "エンゲージメント": "likes, comments, and shares",
    "集客・販売": "driving traffic or sales",
    "情報シェア": "sharing useful information",
    "ブランディング": "personal or company branding",
}


def render():
    st.header(":material/tag: SNS投稿文作成")
    st.caption("各SNSの特性に合わせた投稿文を生成します")

    topic = st.text_area(
        "投稿のテーマ・内容 *",
        placeholder="例: 新しいカフェをオープンしました。場所は渋谷で、オーガニックコーヒーが売り。",
        height=120,
    )

    col1, col2 = st.columns(2)
    with col1:
        platform = st.selectbox("プラットフォーム", list(PLATFORMS.keys()))
        goal = st.selectbox("投稿の目的", list(GOALS.keys()))
    with col2:
        count = st.slider("生成するパターン数", min_value=1, max_value=5, value=3)
        hashtags = st.text_input("含めたいハッシュタグ（任意）", placeholder="例: #カフェ #渋谷 #コーヒー")

    if st.button("投稿文を生成", type="primary", use_container_width=True):
        if not topic:
            st.warning("投稿のテーマ・内容を入力してください")
            return
        if len(topic) > 2000:
            st.warning(f"テーマ・内容が長すぎます（{len(topic):,}字）。2,000字以内にしてください。")
            return

        p = PLATFORMS[platform]
        hashtag_text = f"\n必ず含めるハッシュタグ: {hashtags}" if hashtags else ""

        prompt = f"""あなたはSNSマーケティングのプロです。以下の条件で{platform}用の投稿文を{count}パターン作成してください。

【テーマ・内容】
{topic}

【条件】
プラットフォーム: {platform}
特性: {p["desc"]}
文字数制限: {p["limit"]}
投稿目的: {GOALS[goal]}
言語: 日本語{hashtag_text}

【出力形式】
各パターンを以下の形式で出力してください:

### パターン1
（投稿文）

### パターン2
（投稿文）

のように{count}パターン出力してください。各パターンは明確に異なるアプローチで。"""

        try:
            with st.spinner("投稿文を生成中..."):
                result = generate(prompt)
        except RuntimeError as e:
            st.error(str(e))
            return

        title = f"{platform} - {topic[:30].strip()}..."
        st.session_state["social_post_result"] = {"content": result, "title": title}

    # 生成結果の表示
    saved = st.session_state.get("social_post_result")
    if saved:
        result = saved["content"]
        st.divider()
        st.subheader("生成された投稿文")
        st.markdown(result)

        col_dl, col_save = st.columns(2)
        with col_dl:
            st.download_button(
                "📄 投稿文をダウンロード",
                data=result,
                file_name="social_posts.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_save:
            if st.button("保存", icon=":material/save:", use_container_width=True):
                history_utils.save_entry("SNS投稿文作成", saved["title"], result)
                st.success("保存しました！")
