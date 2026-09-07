from __future__ import annotations

from typing import Callable, Optional

from utils.gemini import generate
from utils import guardrail

# 進捗をUIに伝えるためのコールバック（省略可）
ProgressCb = Optional[Callable[[str], None]]


def _notify(cb: ProgressCb, msg: str) -> None:
    if cb:
        cb(msg)


# --- Planner Agent（構成・共感設計） ---------------------------------------

def plan_structure(
    theme: str,
    target: str = "",
    keywords: str = "",
    extra: str = "",
) -> str:
    prompt = f"""あなたは読者心理に詳しいコンテンツ設計者です。
本文を書く前の「設計図」だけを作成してください。本文は書かないでください。

テーマ: {theme}
ターゲット読者: {target or "指定なし"}
キーワード: {keywords or "指定なし"}
補足: {extra or "なし"}

次の項目を日本語の箇条書きで整理してください:

1. 読者の悩み・不安（具体的なシーンを2〜3個。「〇〇しようとして△△で困る」の形で）
2. 検索意図（読者はこの記事に何を期待して検索したか。1〜2文）
3. 共感エピソードの核（実体験風に語れる小さな物語の骨子を1〜2個。時・場所・気持ちを添える）
4. 記事の構成案（H2/H3見出しのリスト。各見出しで「何を伝えるか」を一言添える）
5. 各セクションに入れる具体例・数字・事例のアイデア

設計図のみを簡潔に出力してください。"""
    return generate(prompt)


# --- Writer Agent（初稿作成） ---------------------------------------------

def write_draft(
    theme: str,
    plan_text: str,
    target: str = "",
    keywords: str = "",
    char_count: int = 1000,
    tone_ja: str = "フレンドリーで親しみやすい",
    extra: str = "",
) -> str:
    prompt = f"""あなたはプロのブログライターです。
以下の「設計図」に忠実に従って、日本語のブログ記事の初稿を執筆してください。

テーマ: {theme}
文体: {tone_ja}
文字数: 約{char_count}字
ターゲット読者: {target or "指定なし"}
キーワード: {keywords or "指定なし"}
追加指示: {extra or "なし"}

【設計図】
{plan_text}

【執筆ルール】
- 冒頭に「# 【記事タイトル】」を1行で置く（クリックしたくなるタイトル、メインキーワードを含める）
- 各見出しは「## 【見出し名】」、小見出しは「### 【小見出し名】」の形式
- 「## 【はじめに】」は設計図の悩み・共感エピソードから書き始める
- 各セクションに設計図の具体例・数字・事例を必ず1つ以上入れる
- 「## 【まとめ】」で要点を箇条書きにし、読者への次の一歩を提案する
- 導入文の冒頭100字以内にメインキーワードを自然に入れる

Markdown形式で記事本文のみを出力してください。"""
    return generate(prompt)


# --- Polisher Agent（脱AI校正・人間の揺らぎ追加） ------------------------

POLISH_RULES = """【脱AIルール】
- 定型的な接続詞（「さらに」「また」「そして」「まとめとして」「加えて」など）を減らし、
  使うとしても記事全体で数回までにする。文どうしのつながりは内容で見せる。
- 「〜と言えるでしょう」「〜について解説します」「いかがでしたでしょうか」といった
  常套句は使わない。
- 1文が長くなりすぎないようにする（目安として1文100字以内）。
- 断定と問いかけを織り交ぜる（「〜です。」ばかりにせず、時々読者に問いかける）。
- 口語的で親しみやすい表現に整える。体験談的な描写や具体的な情景を1箇所以上残す・足す。
- 段落ごとに、その段落の要点や読者への共感が伝わる一言を入れる。
- 事実・見出し構成・キーワードは変えない。情報を削らない。"""


def polish_text(draft: str, fewshot: str = "", feedback: str = "") -> str:
    fewshot_block = f"\n\n{fewshot}\n" if fewshot else ""
    feedback_block = (
        f"\n\n【前回の校正で指摘された問題（必ず直すこと）】\n{feedback}\n" if feedback else ""
    )
    prompt = f"""あなたは「AIっぽさ」を消すのが得意な日本語エディターです。
以下の記事を、意味と構成を保ったまま、人間が書いたような自然な文章に整えてください。

{POLISH_RULES}
{fewshot_block}{feedback_block}
【対象の記事】
{draft}

整えた記事の全文のみをMarkdown形式で出力してください。"""
    return generate(prompt)


# --- オーケストレーション -------------------------------------------------

def run_pipeline(
    theme: str,
    target: str = "",
    keywords: str = "",
    char_count: int = 1000,
    tone_ja: str = "フレンドリーで親しみやすい",
    extra: str = "",
    fewshot: str = "",
    max_retries: int = 1,
    progress: ProgressCb = None,
) -> dict:
    """Planner → Writer → Polisher → ガードレール判定（未達なら再校正）。

    戻り値: {"plan", "draft", "final", "guardrail", "retries"}
    """
    _notify(progress, "① 構成・共感設計（Planner）")
    plan_text = plan_structure(theme, target, keywords, extra)

    _notify(progress, "② 初稿作成（Writer）")
    draft = write_draft(theme, plan_text, target, keywords, char_count, tone_ja, extra)

    _notify(progress, "③ 脱AI校正（Polisher）")
    final = polish_text(draft, fewshot=fewshot)

    report = guardrail.evaluate(final)
    retries = 0
    while not report.passed and retries < max_retries:
        retries += 1
        _notify(progress, f"④ ガードレール未達 → 再校正 {retries}/{max_retries}")
        final = polish_text(draft, fewshot=fewshot, feedback=report.feedback_text())
        report = guardrail.evaluate(final)

    return {
        "plan": plan_text,
        "draft": draft,
        "final": final,
        "guardrail": report,
        "retries": retries,
    }
