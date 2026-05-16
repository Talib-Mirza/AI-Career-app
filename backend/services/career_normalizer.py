"""Normalize free-form learning goals into a short snake_case label for logging and UI metadata.

The input may be a career, course, concept, idea, hobby, project, skill — not necessarily a job title."""

from __future__ import annotations

import re

import httpx

from app.core.config import settings


NORMALIZE_PROMPT = """The user describes something they want to learn or explore. It might be:
- a career or job path
- a course or credential track
- a concept, theory, or field of study
- a product idea, side project, or creative goal
- a skill, tool, stack, or hobby

Produce ONE concise snake_case identifier that captures the core learning focus (not a full sentence).
Return ONLY that identifier, no quotes or explanation.

Examples:
ai_engineering
watercolor_fundamentals
stoicism_intro
validate_saas_idea
dental_hygiene_board_prep
rust_async_concurrency
figma_ui_systems

User input:
{user_query}
"""


class CareerNormalizer:
    """Backward-compatible name; normalizes arbitrary learning intents, not only careers."""

    async def normalize_learning_focus(self, query: str) -> str:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")

        prompt = NORMALIZE_PROMPT.format(user_query=query)
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 48,
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        raw = str(data["choices"][0]["message"]["content"] or "").strip().lower()
        raw = raw.splitlines()[0].strip() if raw else ""
        normalized = re.sub(r"[^a-z0-9_]+", "_", raw)
        normalized = re.sub(r"_+", "_", normalized).strip("_")

        if not normalized:
            fallback = re.sub(r"[^a-z0-9]+", "_", query.lower())
            normalized = re.sub(r"_+", "_", fallback).strip("_") or "learning_goal"

        return normalized

    async def normalize_career(self, query: str) -> str:
        """Deprecated alias for ``normalize_learning_focus``."""
        return await self.normalize_learning_focus(query)
