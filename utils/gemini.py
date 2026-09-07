"""LLM クライアント（Google Gemini / Anthropic Claude 両対応）。

API キーの先頭で自動判別する:
- `sk-ant-...` → Anthropic Claude
- それ以外（`AIza...` など） → Google Gemini

各ツールは `from utils.gemini import generate` で呼び出す（プロバイダは透過）。
"""
from __future__ import annotations

import os

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from dotenv import load_dotenv

load_dotenv()

# モデル選択肢（サイドバーのフォールバック用）
ANTHROPIC_MODELS = ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"]
DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

_QUOTA_MSG = (
    "クォータ（利用上限）を超えました。\n\n"
    "**対処法:**\n"
    "- しばらく待ってから再試行する（1分後、または翌日にリセット）\n"
    "- サイドバーで別のモデルに切り替える\n"
    "- 課金を有効にする（Google AI Studio / Anthropic Console）"
)
_BAD_KEY_MSG = "API キーが無効です。サイドバーから正しいキーを入力してください。"
_GENERIC_MSG = "生成中にエラーが発生しました。しばらくしてから再試行してください。"

_provider: str | None = None            # "gemini" | "anthropic"
_gemini_model = None
_anthropic_client = None
_anthropic_model_name = DEFAULT_ANTHROPIC_MODEL


# --- キー解決 -------------------------------------------------------------

def get_api_key() -> str:
    """API キーを 環境変数(.env) → Streamlit Secrets の順で探す。

    `GEMINI_API_KEY` と `ANTHROPIC_API_KEY` の両方を見る。
    """
    names = ("GEMINI_API_KEY", "ANTHROPIC_API_KEY")
    for name in names:
        v = os.getenv(name, "")
        if v:
            return v
    try:
        import streamlit as st

        for name in names:
            v = str(st.secrets.get(name, "") or "")
            if v:
                return v
    except Exception:
        pass
    return ""


def detect_provider(api_key: str) -> str:
    return "anthropic" if api_key.strip().startswith("sk-ant-") else "gemini"


def get_provider() -> str | None:
    return _provider


# --- 初期化 -------------------------------------------------------------

def init_model(api_key: str | None = None, model_name: str | None = None):
    """キーの種類に応じて Gemini / Anthropic のクライアントを用意する。"""
    global _provider, _gemini_model, _anthropic_client, _anthropic_model_name

    key = api_key or get_api_key()
    if not key:
        raise ValueError("API キーが設定されていません")

    _provider = detect_provider(key)

    if _provider == "anthropic":
        import anthropic

        _anthropic_client = anthropic.Anthropic(api_key=key)
        _anthropic_model_name = model_name or DEFAULT_ANTHROPIC_MODEL
        return _anthropic_client

    genai.configure(api_key=key)
    _gemini_model = genai.GenerativeModel(model_name or DEFAULT_GEMINI_MODEL)
    return _gemini_model


def get_model():
    if _provider == "anthropic":
        if _anthropic_client is None:
            raise ValueError("モデルが初期化されていません。先に init_model() を呼んでください")
        return _anthropic_client
    if _gemini_model is None:
        raise ValueError("モデルが初期化されていません。先に init_model() を呼んでください")
    return _gemini_model


def list_available_models() -> list[str]:
    """サイドバーのモデル選択肢。"""
    if _provider == "anthropic":
        return list(ANTHROPIC_MODELS)
    try:
        models = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        return sorted(models)
    except Exception:
        return ["gemini-2.0-flash"]


# --- 生成 -------------------------------------------------------------

def _generate_gemini(prompt: str, model=None) -> str:
    m = model or _gemini_model
    if m is None:
        raise ValueError("モデルが初期化されていません")
    try:
        return m.generate_content(prompt).text
    except ResourceExhausted:
        raise RuntimeError(_QUOTA_MSG)
    except InvalidArgument:
        raise RuntimeError(_BAD_KEY_MSG)
    except Exception:
        raise RuntimeError(_GENERIC_MSG)


def _generate_anthropic(prompt: str) -> str:
    import anthropic

    if _anthropic_client is None:
        raise ValueError("モデルが初期化されていません")
    try:
        resp = _anthropic_client.messages.create(
            model=_anthropic_model_name,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return text.strip()
    except anthropic.RateLimitError:
        raise RuntimeError(_QUOTA_MSG)
    except anthropic.AuthenticationError:
        raise RuntimeError(_BAD_KEY_MSG)
    except anthropic.NotFoundError:
        raise RuntimeError(
            "選択したモデルにアクセスできません。サイドバーで別の Claude モデルに切り替えてください。"
        )
    except anthropic.APIStatusError as e:
        if getattr(e, "status_code", 0) >= 500:
            raise RuntimeError("サーバーエラーが発生しました。しばらくしてから再試行してください。")
        raise RuntimeError(_GENERIC_MSG)
    except Exception:
        raise RuntimeError(_GENERIC_MSG)


def generate(prompt: str, model=None) -> str:
    if _provider == "anthropic":
        return _generate_anthropic(prompt)
    return _generate_gemini(prompt, model)
