"""LLM client wrapper for the Anthropic SDK"""

import json
import os
import time
from pathlib import Path

try:
    from anthropic import Anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 2000


def _config_path() -> Path:
    return Path.home() / ".dlc" / "config.json"


def _load_config() -> dict:
    try:
        return json.loads(_config_path().read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def get_api_key() -> str | None:
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    return _load_config().get("anthropic_api_key")


def set_api_key(key: str) -> None:
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    cfg: dict = {}
    if p.exists():
        try:
            cfg = json.loads(p.read_text())
        except json.JSONDecodeError:
            cfg = {}
    cfg["anthropic_api_key"] = key
    p.write_text(json.dumps(cfg, indent=2))


def has_api_key() -> bool:
    return bool(get_api_key())


def call_llm(
    prompt: str,
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    system: str | None = None,
) -> dict:
    if not _ANTHROPIC_AVAILABLE:
        return {
            "ok": False, "text": None,
            "error": "anthropic SDK not installed (uv add anthropic)",
            "usage": None, "model": model,
        }
    key = api_key or get_api_key()
    if not key:
        return {
            "ok": False, "text": None,
            "error": (
                "No ANTHROPIC_API_KEY found. Set the env var or save "
                "it via the API-key chip in the toolbar."
            ),
            "usage": None, "model": model,
        }
    client = Anthropic(api_key=key)
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system or "You are a helpful circuit reasoning assistant.",
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(
                block.text for block in resp.content if getattr(block, "type", None) == "text"
            )
            return {
                "ok": True, "text": text, "error": None,
                "usage": {
                    "input_tokens": resp.usage.input_tokens,
                    "output_tokens": resp.usage.output_tokens,
                },
                "model": model,
            }
        except Exception as exc:
            last_err = exc
            msg = str(exc).lower()
            if ("rate" in msg or "429" in msg or "overload" in msg) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            break
    return {
        "ok": False, "text": None,
        "error": f"{type(last_err).__name__ if last_err else 'Error'}: {last_err}",
        "usage": None, "model": model,
    }