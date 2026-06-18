from __future__ import annotations
import streamlit as st
from utils.gemini import generate
from utils import history as history_utils


TONES = {
    "丁寧・ビジネス": "polite and professional business Japanese",
    "フレンドリー": "friendly and warm",
    "簡潔・シンプル": "concise and to the point",
    "フォーマル": "very formal and respectful",
}

REPLY_TYPES = {
    "承諾・OK": "accepting / agreeing",
    "断り・お断り": "politely declining",
    "確認・質問": "asking for clarification or additional information",
    "お礼": "expressing gratitude",
    "謝罪": "apologizing",
    "情報提供": "providing requested information",
}


def render():
    st.header("📧 メール返信作成")
    st.caption("受信したメールを貼り付けるだけで、適切な返信文を生成します")

    received = st.text_area(
        "受信メール本文 *",
        placeholder="ここに返信したいメールの本文を貼り付けてください...",
        height=180,
    )

    col1, col2 = st.columns(2)
    with col1:
        reply_type = st.selectbox("返信の種類", list(REPLY_TYPES.keys()))
        tone = st.selectbox("文体・トーン", list(TONES.keys()))
    with col2:
        your_name = st.text_input("差出人名（任意）", placeholder="例: 山田 太郎")
        context = st.text_input("補足・背景情報（任意）", placeholder="例: 来週は出張中のため対応が遅れる")

    extra = st.text_area("伝えたい内容・追加事項（任意）", placeholder="例: 会議は木曜14時なら参加可能です", height=80, max_chars=300)

    if st.button("返信文を生成", type="primary", use_container_width=True):
        if not received:
            st.warning("受信メールの本文を入力してください")
            return
        if len(received) > 5000:
            st.warning(f"メール本文が長すぎます（{len(received):,}字）。5,000字以内にしてください。")
            return

        reply_en = REPLY_TYPES[reply_type]
        tone_en = TONES[tone]
        name_text = f"差出人名: {your_name}" if your_name else ""
        context_text = f"背景情報: {context}" if context else ""
        extra_text = f"返信で伝えたい内容: {extra}" if extra else ""

        prompt = f"""あなたはビジネスメールのプロライターです。以下の受信メールに対する返信文を日本語で作成してください。

【受信メール】
{received}

【返信の条件】
返信種別: {reply_en}
文体: {tone_en}（日本語）
{name_text}
{context_text}
{extra_text}

【出力形式】
件名: （適切な件名）

（本文）

---
・宛名・本文・締め括りを含む完全な返信メールを作成してください
・自然で読みやすい日本語にしてください"""

        try:
            with st.spinner("返信文を生成中..."):
                result = generate(prompt)
        except RuntimeError as e:
            st.error(str(e))
            return

        title = f"メール返信 - {received[:30].strip()}..."
        st.session_state["email_reply_result"] = {"content": result, "title": title}

    # 生成結果の表示
    saved = st.session_state.get("email_reply_result")
    if saved:
        result = saved["content"]
        st.divider()
        st.subheader("生成された返信文")
        st.text_area("返信文（コピーしてお使いください）", value=result, height=300)

        col_save, _ = st.columns([1, 2])
        with col_save:
            if st.button("💾 保存", use_container_width=True):
                history_utils.save_entry("メール返信作成", saved["title"], result)
                st.success("保存しました！")
