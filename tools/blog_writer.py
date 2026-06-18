from __future__ import annotations
import io
import re
import streamlit as st
from docx import Document
from utils.gemini import generate
from utils import history as history_utils


def _add_paragraph_with_bold(doc: Document, text: str, style: str | None = None) -> None:
    """**囲みを太字runとして段落に追加する"""
    para = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    parts = re.split(r"\*\*", text)
    for i, part in enumerate(parts):
        run = para.add_run(part)
        run.bold = (i % 2 == 1)


def _to_docx(markdown_text: str) -> bytes:
    doc = Document()
    for line in markdown_text.splitlines():
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith("- ") or line.startswith("* "):
            _add_paragraph_with_bold(doc, line[2:].strip(), style="List Bullet")
        elif re.match(r"^\d+\. ", line):
            _add_paragraph_with_bold(doc, re.sub(r"^\d+\. ", "", line).strip(), style="List Number")
        elif line.strip():
            _add_paragraph_with_bold(doc, line.strip())
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


TONES = {
    "プロフェッショナル": "professional, authoritative, informative",
    "フレンドリー": "friendly, casual, approachable",
    "エンタメ系": "entertaining, engaging, light-hearted",
    "教育的": "educational, clear, step-by-step",
}

LENGTHS = {
    "短め (500字程度)": 500,
    "標準 (1000字程度)": 1000,
    "詳細 (2000字程度)": 2000,
}


def render():
    st.header("✍️ ブログ記事作成")
    st.caption("テーマとキーワードを入力するだけで、構成付きのブログ記事を生成します")

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("記事タイトル / テーマ *", placeholder="例: 初心者向けPython入門ガイド")
        tone = st.selectbox("文体・トーン", list(TONES.keys()))
    with col2:
        keywords = st.text_input("キーワード（カンマ区切り）", placeholder="例: Python, プログラミング, 入門")
        length = st.selectbox("文章量", list(LENGTHS.keys()))

    target = st.text_input("ターゲット読者", placeholder="例: プログラミング未経験の社会人")
    extra = st.text_area("追加の指示・補足（任意）", placeholder="例: SEOを意識した構成にしてください", height=80, max_chars=300)

    if st.button("記事を生成", type="primary", use_container_width=True):
        if not title:
            st.warning("記事タイトル / テーマを入力してください")
            return
        if len(title) > 200:
            st.warning("タイトルが長すぎます（200字以内）")
            return

        char_count = LENGTHS[length]
        tone_en = TONES[tone]
        kw_text = f"キーワード: {keywords}" if keywords else ""
        target_text = f"ターゲット読者: {target}" if target else ""
        extra_text = f"追加指示: {extra}" if extra else ""

        prompt = f"""あなたはプロのブログライターです。以下の条件に従って日本語のブログ記事を作成してください。

タイトル: {title}
文体: {tone_en}（日本語で）
文字数: 約{char_count}字
{kw_text}
{target_text}
{extra_text}

【タイトルについて】
- 読者が思わずクリックしたくなる、魅力的で興味を引くタイトルを考えてください
- 記事の冒頭に「# 【タイトル】」の形式で表示してください

【SEO条件】
- タイトルにメインキーワードを含めてください
- 導入文の冒頭100字以内にメインキーワードを自然に入れてください
- 見出し（H2・H3）にも関連キーワードを散りばめてください
- 同じキーワードを不自然に繰り返さず、共起語・関連語も使ってください
- 読者の検索意図（知りたい・やりたい・悩んでいる）に応える内容にしてください

【構成について】
以下の構成で、各見出しは「## 【見出し名】」の形式で書いてください:

1. ## 【はじめに】
   - 読者が共感できる悩みや疑問から書き始めてください
   - この記事を読むと何が得られるかを明示してください

2. ## 【本文の各セクション】
   - 内容を複数のセクションに分けて整理してください
   - 各セクションには具体的な例・事例・数字を必ず含めてください
   - 必要に応じて「### 【小見出し】」も活用してください

3. ## 【まとめ】
   - 記事全体の要点を箇条書きで整理してください
   - 読者への次のアクションを提案してください

Markdown形式で出力してください。"""

        try:
            with st.spinner("記事を生成中..."):
                result = generate(prompt)
        except RuntimeError as e:
            st.error(str(e))
            return

        st.session_state["blog_writer_result"] = {"content": result, "title": title}

    # 生成結果の表示
    saved = st.session_state.get("blog_writer_result")
    if saved:
        result = saved["content"]
        st.divider()
        st.subheader("生成結果")
        st.markdown(result)

        col_dl1, col_dl2, col_save = st.columns(3)
        with col_dl1:
            st.download_button(
                "📄 テキスト (.txt)",
                data=result,
                file_name="blog_article.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_dl2:
            st.download_button(
                "📝 Word (.docx)",
                data=_to_docx(result),
                file_name="blog_article.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with col_save:
            if st.button("💾 保存", use_container_width=True):
                history_utils.save_entry("ブログ記事作成", saved["title"], result)
                st.success("保存しました！")
