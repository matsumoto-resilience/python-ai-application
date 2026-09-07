"""明るいクリーン方向の見た目を Streamlit に適用するためのヘルパー。

- inject_global_css(): 全画面共通の CSS（フォント・カード・ボタン・サイドバー等）
- render_score_panel(): ガードレールの品質スコアをゲージ + バーで表示
- SVG / HTML は ai-writing-redesign.html のデザインに合わせている
"""
from __future__ import annotations

import html
import math

import streamlit as st

FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Poppins:wght@500;600;700;800&"
    "family=Noto+Sans+JP:wght@400;500;700;800&display=swap"
)

# パレット（デザイン仕様と一致）
BLUE = "#4a7be5"
BLUE_DARK = "#3a63c8"
BLUE_SOFT = "#e9f0fd"
BLUE_INK = "#2f56b8"
INK = "#1e2431"
INK_2 = "#697386"
INK_3 = "#9aa2b1"
LINE = "#e8ebf2"
SOFT = "#f6f8fc"
GREEN = "#2fb968"
GREEN_SOFT = "#e6f7ee"
AMBER = "#efa63c"
AMBER_SOFT = "#fdf1de"

_DISPLAY = "'Poppins','Noto Sans JP','Hiragino Kaku Gothic ProN',sans-serif"
_BODY = "'Noto Sans JP','Hiragino Kaku Gothic ProN','Helvetica Neue',Arial,sans-serif"


def inject_global_css() -> None:
    """全画面共通のスタイル。app.py の最初に一度呼ぶ。"""
    st.markdown(
        f"""
<style>
@import url('{FONT_URL}');

:root {{
  --blue:{BLUE}; --blue-dark:{BLUE_DARK}; --blue-soft:{BLUE_SOFT}; --blue-ink:{BLUE_INK};
  --ink:{INK}; --ink-2:{INK_2}; --ink-3:{INK_3};
  --line:{LINE}; --soft:{SOFT};
  --shadow-sm:0 1px 2px rgba(30,41,59,.06),0 2px 8px rgba(30,41,59,.05);
  --shadow-md:0 10px 34px rgba(40,56,100,.10);
}}

/* --- 下地 --- */
.stApp {{ background:#f4f6fb; }}
/* 画面幅に追従（上限だけゆるく設定）。縦スクロールは stMain に任せる */
.stMainBlockContainer {{
  max-width: min(1400px, 100%);
  padding-top: 2.4rem; padding-bottom: 4rem;
}}
section[data-testid="stMain"] {{ overflow-y: auto !important; }}

html, body, .stApp, .stMarkdown, p, li, label, span, div, input, textarea, button {{
  font-family:{_BODY};
}}
h1,h2,h3,h4,h5 {{ font-family:{_DISPLAY} !important; color:var(--ink); letter-spacing:.01em; }}
h1, h2 {{ font-weight:800 !important; }}
h3, h4 {{ font-weight:700 !important; }}
.stMarkdown p, .stMarkdown li {{ color:#37414f; }}
label p, [data-testid="stWidgetLabel"] p {{ font-weight:600 !important; color:var(--ink-2); }}

/* --- アイコン：見出し・サイドバーのナビだけ細いモノラインに（システムのアラート/状態アイコンは触らない） --- */
[data-testid="stHeading"] span[translate="no"],
[data-testid="stHeadingWithActionElements"] span[translate="no"],
section[data-testid="stSidebar"] div[role="radiogroup"] span[translate="no"] {{
  font-variation-settings: 'FILL' 0, 'wght' 300, 'opsz' 24 !important;
}}
/* 見出し内アイコンは少し小さめ＆余白 */
[data-testid="stHeading"] span[translate="no"],
[data-testid="stHeadingWithActionElements"] span[translate="no"] {{
  font-size: 0.86em; margin-right: .14em; color: var(--blue); vertical-align: -0.06em;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] span[translate="no"] {{ font-size: 1.1rem; }}

/* --- 実行中インジケーター：Streamlit の「走る人」を消してシンプルな回転スピナーに --- */
[data-testid="stStatusWidget"] img,
[data-testid="stStatusWidget"] svg:first-child,
[data-testid="stAppRunningIcon"] {{ display: none !important; }}
[data-testid="stStatusWidget"] {{ display: flex; align-items: center; gap: 6px; }}
[data-testid="stStatusWidget"]::before {{
  content: ""; width: 13px; height: 13px; flex-shrink: 0;
  border: 2px solid var(--blue-soft); border-top-color: var(--blue);
  border-radius: 50%; animation: ai-spin .7s linear infinite;
}}
@keyframes ai-spin {{ to {{ transform: rotate(360deg); }} }}

/* --- サイドバー --- */
section[data-testid="stSidebar"] {{ background:#fff; border-right:1px solid var(--line); }}
section[data-testid="stSidebar"] .stHeadingContainer h1,
section[data-testid="stSidebar"] h1 {{ font-size:1.15rem; }}

/* ツール選択の st.radio をナビ風に */
section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap:2px; }}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {{
  padding:9px 12px; border-radius:12px; margin:0; width:100%;
  transition:background .12s ease;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{ background:var(--soft); }}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{ background:var(--blue-soft); }}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {{
  color:var(--blue-ink); font-weight:600;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {{ display:none; }}
section[data-testid="stSidebar"] div[role="radiogroup"] p {{ font-family:{_DISPLAY}; font-size:.9rem; }}

/* --- ボタン --- */
.stButton > button, .stDownloadButton > button {{
  border-radius:13px; font-family:{_DISPLAY}; font-weight:600;
  border:1px solid var(--line); box-shadow:none; transition:all .12s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color:var(--blue); color:var(--blue); }}
.stButton > button[kind="primary"] {{
  background:var(--blue); border-color:var(--blue); color:#fff;
  box-shadow:0 8px 20px rgba(74,123,229,.28);
}}
.stButton > button[kind="primary"]:hover {{
  background:var(--blue-dark); border-color:var(--blue-dark); color:#fff;
}}

/* --- 入力 --- */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
div[data-baseweb="select"] > div {{
  background:var(--soft) !important; border-radius:12px !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
  border-color:var(--blue) !important; box-shadow:0 0 0 3px rgba(74,123,229,.14) !important;
}}

/* --- Expander / bordered container をカードに --- */
div[data-testid="stExpander"] {{
  border:1px solid var(--line); border-radius:14px; background:#fff;
  box-shadow:var(--shadow-sm);
}}
/* Vega/Altair がホイールを奪ってスクロールが止まるのを防ぐ */
div[data-testid="stVegaLiteChart"], div[data-testid="stVegaLiteChart"] * {{ overscroll-behavior: auto; }}
div[data-testid="stExpander"] summary:hover {{ color:var(--blue); }}
div[data-testid="stVerticalBlockBorderWrapper"] {{
  border-radius:18px !important; border-color:var(--line) !important;
  background:#fff; box-shadow:var(--shadow-md);
}}

/* --- メトリクスをタイルに --- */
div[data-testid="stMetric"] {{
  background:#fff; border:1px solid var(--line); border-radius:16px;
  padding:16px 18px; box-shadow:var(--shadow-sm);
}}
div[data-testid="stMetricValue"] {{ font-family:{_DISPLAY}; font-weight:700; color:var(--ink); }}
div[data-testid="stMetricLabel"] p {{ font-family:{_DISPLAY}; font-weight:600; color:var(--ink-3); }}

/* --- 区切り線を控えめに --- */
hr {{ border-color:var(--line); }}

/* --- st.status / alert の角丸 --- */
div[data-testid="stStatusWidget"], div[data-testid="stAlert"] {{ border-radius:14px; }}
</style>
""",
        unsafe_allow_html=True,
    )


def _bar(label: str, value: int) -> str:
    v = max(0, min(100, int(value)))
    return (
        '<div style="display:flex;align-items:center;gap:12px;margin:9px 0">'
        f'<span style="width:118px;font-size:12px;color:{INK_2};flex-shrink:0">{html.escape(label)}</span>'
        f'<span style="flex:1;height:8px;border-radius:4px;background:{BLUE_SOFT};overflow:hidden">'
        f'<span style="display:block;height:100%;width:{v}%;background:{BLUE};border-radius:4px"></span></span>'
        f'<span style="width:28px;text-align:right;font-family:{_DISPLAY};font-weight:700;'
        f'font-size:12px;color:{INK};flex-shrink:0">{v}</span></div>'
    )


def render_score_panel(score: int, passed: bool, dims: list[tuple[str, int]] | None = None) -> None:
    """ガードレールの品質スコアをゲージ + 内訳バーで表示する。"""
    score = max(0, min(100, int(score)))
    r = 58
    circ = 2 * math.pi * r
    dash = score / 100 * circ
    arc = GREEN if passed else AMBER
    _dot = ('<span style="width:6px;height:6px;border-radius:50%;background:currentColor;'
            'display:inline-block"></span>')
    if passed:
        pill = (
            f'<span style="display:inline-flex;align-items:center;gap:7px;background:{GREEN_SOFT};'
            f'color:#1e8f4e;font-family:{_DISPLAY};font-weight:700;font-size:11px;'
            f'border-radius:999px;padding:5px 12px">{_dot}ガードレール合格</span>'
        )
    else:
        pill = (
            f'<span style="display:inline-flex;align-items:center;gap:7px;background:{AMBER_SOFT};'
            f'color:#b9791d;font-family:{_DISPLAY};font-weight:700;font-size:11px;'
            f'border-radius:999px;padding:5px 12px">{_dot}ガードレール未達</span>'
        )
    bars = "".join(_bar(label, v) for label, v in (dims or []))
    if not bars:
        bars = (
            f'<div style="font-size:12px;color:{INK_3};margin-top:6px">'
            "内訳スコアは LLM 評価を実行したときに表示されます</div>"
        )

    st.markdown(
        f"""
<div style="display:flex;gap:28px;align-items:center;background:#fff;border:1px solid {LINE};
     border-radius:20px;box-shadow:0 10px 34px rgba(40,56,100,.10);padding:22px 26px;margin:6px 0 8px">
  <div style="position:relative;width:140px;height:140px;flex-shrink:0">
    <svg width="140" height="140" viewBox="0 0 148 148" fill="none">
      <circle cx="74" cy="74" r="58" stroke="{BLUE_SOFT}" stroke-width="13"/>
      <circle cx="74" cy="74" r="58" stroke="{arc}" stroke-width="13" stroke-linecap="round"
              stroke-dasharray="{dash:.1f} {circ:.1f}" transform="rotate(-90 74 74)"/>
    </svg>
    <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
      <span style="font-family:{_DISPLAY};font-weight:700;font-size:32px;color:{INK};line-height:1">{score}</span>
      <span style="font-family:{_DISPLAY};font-size:10px;color:{INK_3};font-weight:600;margin-top:3px">/ 100</span>
    </div>
  </div>
  <div style="flex:1">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <span style="font-family:{_DISPLAY};font-weight:700;font-size:14px;color:{INK}">品質スコア</span>
      {pill}
    </div>
    {bars}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
