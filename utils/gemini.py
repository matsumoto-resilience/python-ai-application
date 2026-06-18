from __future__ import annotations
import os
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from dotenv import load_dotenv

load_dotenv()

_model = None


def init_model(api_key: str | None = None, model_name: str = "gemini-2.5-flash") -> genai.GenerativeModel:
    global _model
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY が設定されていません")
    genai.configure(api_key=key)
    _model = genai.GenerativeModel(model_name)
    return _model


def get_model() -> genai.GenerativeModel:
    if _model is None:
        raise ValueError("モデルが初期化されていません。先に init_model() を呼んでください")
    return _model


def list_available_models() -> list[str]:
    """generateContent をサポートするモデル名一覧を返す"""
    try:
        models = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        return sorted(models)
    except Exception:
        return ["gemini-2.0-flash"]


def generate(prompt: str, model: genai.GenerativeModel | None = None) -> str:
    m = model or get_model()
    try:
        response = m.generate_content(prompt)
        return response.text
    except ResourceExhausted:
        raise RuntimeError(
            "クォータ（利用上限）を超えました。\n\n"
            "**対処法:**\n"
            "- しばらく待ってから再試行する（1分後、または翌日にリセット）\n"
            "- サイドバーで別のモデルに切り替える\n"
            "- Google AI Studio で課金を有効にする"
        )
    except InvalidArgument:
        raise RuntimeError("API キーが無効です。サイドバーから正しいキーを入力してください。")
    except Exception:
        raise RuntimeError("生成中にエラーが発生しました。しばらくしてから再試行してください。")
