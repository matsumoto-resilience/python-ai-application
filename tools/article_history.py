from __future__ import annotations
import streamlit as st
from utils import history as history_utils


def render() -> None:
    st.header("📚 保存済み記事")
    st.caption("保存した生成結果の一覧です")

    entries = history_utils.load()

    if not entries:
        st.info("保存された記事はまだありません。各ツールで生成後に「💾 保存」ボタンを押してください。")
        return

    # ツール種別でフィルタリング
    tools = sorted({e["tool"] for e in entries})
    filter_tool = st.selectbox(
        "ツールで絞り込み",
        ["すべて"] + tools,
        label_visibility="collapsed",
    )

    filtered = entries if filter_tool == "すべて" else [e for e in entries if e["tool"] == filter_tool]
    st.caption(f"{len(filtered)} 件")

    for entry in filtered:
        created = entry.get("created_at", "")[:16].replace("T", " ")
        label = f"**{entry['title']}**　`{entry['tool']}`　{created}"

        with st.expander(label):
            st.markdown(entry["content"])
            col_dl, col_del = st.columns([3, 1])
            with col_dl:
                st.download_button(
                    "📄 ダウンロード (.txt)",
                    data=entry["content"],
                    file_name=f"{entry['title'][:30]}.txt",
                    mime="text/plain",
                    key=f"dl_{entry['id']}",
                    use_container_width=True,
                )
            with col_del:
                if st.button("🗑️ 削除", key=f"del_{entry['id']}", use_container_width=True):
                    history_utils.delete_entry(entry["id"])
                    st.rerun()
