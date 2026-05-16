"""Unit tests for transcript sliding window (load module by path to skip agents package __init__)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _load_cm():
    path = _BACKEND_ROOT / "agents" / "conversation_memory.py"
    spec = importlib.util.spec_from_file_location("conversation_memory_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cm = _load_cm()


def test_model_context_tokens_matches_known_substrings() -> None:
    assert cm.model_context_tokens("gpt-5-mini") == 256_000
    assert cm.model_context_tokens("openai/gpt-4o-mini") == 128_000


def test_slice_sliding_window_keeps_recent_turns() -> None:
    long = " word" * 500  # > budget alone
    hist = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old reply"},
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": f"new reply{long}"},
    ]
    window = cm.slice_sliding_window(hist, max_tokens=120)
    assert len(window) >= 1
    assert window[-1]["role"] == "assistant"
    assert "new reply" in window[-1]["content"]


def test_state_without_conversation_history_strips_transcript() -> None:
    state = {"conversation_state": {"phase": "followup", "history": [{"role": "user", "content": "hi"}]}, "x": 1}
    out = cm.state_without_conversation_history(state)
    assert "history" not in (out.get("conversation_state") or {})
    assert out["conversation_state"]["phase"] == "followup"
    assert state["conversation_state"]["history"]


def test_history_token_budget_is_positive() -> None:
    b = cm.history_token_budget("gpt-5-mini")
    assert b >= 1600
