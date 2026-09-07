from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from utils import history as history_utils
from utils import metrics

BLUE = "#4a7be5"
_CAT = ["#2a78d6", "#1baf7a", "#eb6834"]  # 検証済みカテゴリ配色（採用そのまま / 手直し / ボツ）
_AXIS = "#8b93a3"
_GRID = "#e6e9f1"


def _base(chart: alt.Chart) -> alt.Chart:
    return chart.configure_view(strokeWidth=0).configure_axis(
        labelColor=_AXIS, titleColor=_AXIS, gridColor=_GRID, domainColor=_GRID, tickColor=_GRID
    ).configure_legend(labelColor="#4b5563", titleColor="#4b5563")


def _chart_trend(scores: list[int]) -> alt.Chart:
    recent = scores[-20:]
    df = pd.DataFrame({"回": list(range(len(scores) - len(recent) + 1, len(scores) + 1)), "スコア": recent})
    enc_x = alt.X("回:Q", axis=alt.Axis(title=None, tickMinStep=1, grid=False, format="d"))
    enc_y = alt.Y("スコア:Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title=None))
    area = alt.Chart(df).mark_area(color=BLUE, opacity=0.10).encode(x=enc_x, y=enc_y)
    line = alt.Chart(df).mark_line(color=BLUE, strokeWidth=2.5).encode(x=enc_x, y=enc_y)
    dots = alt.Chart(df).mark_point(color=BLUE, filled=True, size=45).encode(
        x=enc_x, y=enc_y, tooltip=["回", "スコア"]
    )
    return _base((area + line + dots).properties(height=240))


def _chart_breakdown(asis: int, edited: int, rejected: int) -> alt.Chart:
    df = pd.DataFrame(
        {"区分": ["採用（そのまま）", "採用（手直し）", "ボツ"], "件数": [asis, edited, rejected]}
    )
    return _base(
        alt.Chart(df)
        .mark_arc(innerRadius=55, stroke="#fff", strokeWidth=2)
        .encode(
            theta=alt.Theta("件数:Q", stack=True),
            color=alt.Color(
                "区分:N",
                scale=alt.Scale(domain=df["区分"].tolist(), range=_CAT),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=["区分", "件数"],
        )
        .properties(height=240)
    )


def _chart_tools(tool_counts: dict) -> alt.Chart:
    df = pd.DataFrame({"ツール": list(tool_counts), "件数": list(tool_counts.values())})
    top = max(df["件数"].max(), 1)
    return _base(
        alt.Chart(df)
        .mark_bar(color=BLUE, cornerRadiusEnd=4, size=16)
        .encode(
            x=alt.X(
                "件数:Q",
                axis=alt.Axis(title=None, grid=False, tickMinStep=1, format="d", tickCount=min(top, 5)),
                scale=alt.Scale(domain=[0, top], nice=False),
            ),
            y=alt.Y("ツール:N", sort="-x", axis=alt.Axis(title=None)),
            tooltip=["ツール", "件数"],
        )
        .properties(height=max(120, 34 * len(df)))
    )


def _render_dashboard() -> None:
    s = metrics.dashboard_summary()

    if not s["generations"] and not s["feedback_total"] and not s["tool_counts"]:
        return

    st.subheader(":material/show_chart: ダッシュボード")
    st.caption("生成した記事の品質スコアとフィードバックの傾向")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("記事生成数", s["total_generations"])
    c2.metric("平均スコア", s["avg_score"] if s["avg_score"] is not None else "—")
    c3.metric("採用率", f"{s['adoption_rate']}%" if s["adoption_rate"] is not None else "—")
    c4.metric("蓄積ログ", f"{s['feedback_total']} 件")

    if len(s["scores"]) >= 2:
        with st.container(border=True):
            st.markdown("**ガードレールスコアの推移**")
            st.caption(f"直近 {min(len(s['scores']), 20)} 回の生成 ・ 0〜100")
            st.altair_chart(_chart_trend(s["scores"]), use_container_width=True)

    # 使えるグラフだけを集めて、数に応じて 1列 / 2列 に振り分ける
    panels = []
    if s["adopted_asis"] + s["adopted_edited"] + s["rejected"] > 0:
        panels.append((
            "フィードバック内訳",
            "採用（そのまま / 手直し）とボツの回数",
            _chart_breakdown(s["adopted_asis"], s["adopted_edited"], s["rejected"]),
        ))
    if s["tool_counts"]:
        panels.append((
            "ツール別 保存数",
            "「保存」した生成結果の内訳",
            _chart_tools(s["tool_counts"]),
        ))

    def _panel(container, title, sub, chart):
        with container.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(sub)
            st.altair_chart(chart, use_container_width=True)

    if len(panels) == 2:
        cols = st.columns(2)
        for col, (title, sub, chart) in zip(cols, panels):
            _panel(col, title, sub, chart)
    elif panels:
        title, sub, chart = panels[0]
        _panel(st, title, sub, chart)


def render() -> None:
    st.header(":material/bookmark: 保存済み記事")
    st.caption("保存した生成結果の一覧です")

    _render_dashboard()

    entries = history_utils.load()

    st.divider()
    st.subheader("記事一覧")

    if not entries:
        st.info("保存された記事はまだありません。各ツールで生成後に「保存」ボタンを押してください。")
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

        col_open, col_del = st.columns([5, 1])
        with col_open:
            with st.expander(label):
                st.markdown(entry["content"])
                st.download_button(
                    "ダウンロード (.txt)",
                    data=entry["content"],
                    file_name=f"{entry['title'][:30]}.txt",
                    mime="text/plain",
                    icon=":material/download:",
                    key=f"dl_{entry['id']}",
                    use_container_width=True,
                )
        with col_del:
            confirm_key = f"delconfirm_{entry['id']}"
            if st.session_state.get(confirm_key):
                if st.button("本当に削除", key=f"del_{entry['id']}", type="primary", use_container_width=True):
                    history_utils.delete_entry(entry["id"])
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
                if st.button("やめる", key=f"delcancel_{entry['id']}", use_container_width=True):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
            else:
                if st.button("削除", icon=":material/delete:", key=f"delask_{entry['id']}", use_container_width=True, help="この記事を削除"):
                    st.session_state[confirm_key] = True
                    st.rerun()
