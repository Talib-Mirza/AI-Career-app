"""Sliding-window transcript for the conversation agent, sized from the active LLM model."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


def load_llm_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return raw.get("llm", {}) or {}

# Conservative context lengths (tokens). Used only for budgeting transcript size.
_CONTEXT_TOKENS_BY_SUBSTRING: tuple[tuple[str, int], ...] = (
    ("gpt-5", 256_000),
    ("gpt-4.1", 128_000),
    ("gpt-4o", 128_000),
    ("gpt-4-turbo", 128_000),
    ("gpt-3.5-turbo", 16_385),
    ("gpt-3.5", 16_385),
    ("gemini-2", 1_048_576),
    ("gemini-1.5", 1_048_576),
    ("gemini", 32_768),
    ("claude", 200_000),
)


def model_context_tokens(model: str) -> int:
    ml = model.lower().strip()
    for needle, tokens in _CONTEXT_TOKENS_BY_SUBSTRING:
        if needle in ml:
            return tokens
    return 128_000


def _history_settings() -> dict[str, Any]:
    cfg = load_llm_config() or {}
    raw = cfg.get("conversation_history") or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def history_token_budget(model: str) -> int:
    """
    Approximate number of tokens we allow for prior user/assistant turns in the prompt.
    Scales with the configured model's context window.
    """
    settings = _history_settings()
    fraction = float(settings.get("fraction_of_context", 0.08))
    reserved = int(settings.get("reserved_tokens", 14_000))
    floor_tokens = int(settings.get("min_history_tokens", 1_600))
    ceiling_tokens = int(settings.get("max_history_tokens", 24_000))

    ctx = model_context_tokens(model)
    usable = max(ctx - reserved, 8_000)
    budget = int(usable * max(0.02, min(fraction, 0.35)))
    return max(floor_tokens, min(budget, ceiling_tokens))


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def slice_sliding_window(history: list[dict[str, Any]], max_tokens: int) -> list[dict[str, Any]]:
    """
    Keep the most recent turns whose total estimated token count stays under max_tokens.
    """
    if not history or max_tokens < 1:
        return []

    selected: list[dict[str, Any]] = []
    used = 0
    for entry in reversed(history):
        role = entry.get("role")
        if role not in ("user", "assistant"):
            continue
        content = str(entry.get("content") or "").strip()
        if not content:
            continue
        t = approx_tokens(content)
        if used + t > max_tokens and selected:
            break
        selected.append({"role": role, "content": content})
        used += t
    return list(reversed(selected))


def state_without_conversation_history(state: dict[str, Any]) -> dict[str, Any]:
    """Deep copy of session state with conversation transcript omitted (it is sent as chat turns)."""
    out = copy.deepcopy(state)
    cs = out.get("conversation_state")
    if isinstance(cs, dict):
        cs.pop("history", None)
        cs["_transcript"] = "Prior user/assistant messages are included as separate chat turns before this prompt."
    return out


def trim_stored_history(history: list[dict[str, Any]], max_messages: int) -> None:
    """Drop oldest entries in place when the buffer grows too large."""
    if max_messages < 4 or len(history) <= max_messages:
        return
    overflow = len(history) - max_messages
    del history[:overflow]


def max_stored_history_messages() -> int:
    return int(_history_settings().get("max_stored_messages", 200))
