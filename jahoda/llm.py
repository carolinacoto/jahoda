"""Thin Anthropic client wrapper: chat, tool-use, retry/backoff, caching.

Used by both the targets (conversation runner) and the verifier (judges). The
two never share a client instance OR message history — judge isolation is
structural (see verifier.py).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import anthropic

log = logging.getLogger("jahoda.llm")

_RETRYABLE = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
    anthropic.RateLimitError,
)


class TargetError(Exception):
    """Raised after retries are exhausted; recorded as target_error, never swallowed."""


def _client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=key, max_retries=0, timeout=60.0)


def _with_retry(fn, *, what: str, max_attempts: int = 4, base: float = 1.5):
    last: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except _RETRYABLE as e:  # transient
            last = e
            wait = base**attempt
            log.warning(
                "retryable error on %s (attempt %d): %s; backoff %.1fs", what, attempt + 1, e, wait
            )
            time.sleep(wait)
        except anthropic.BadRequestError:
            raise  # non-retryable; surface immediately
    raise TargetError(f"{what} failed after {max_attempts} attempts: {last}")


def chat(
    *,
    model: str,
    system: str,
    messages: list[dict[str, Any]],
    max_tokens: int = 1024,
    temperature: float = 0.0,
    cache_system: bool = False,
) -> str:
    """Plain text completion. Used to generate a target's next turn."""
    client = _client()
    system_param: Any = system
    if cache_system and system:
        system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

    def call():
        return client.messages.create(
            model=model,
            system=system_param,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    resp = _with_retry(call, what=f"chat[{model}]")
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def tool_verdict(
    *,
    model: str,
    system_blocks: list[dict[str, Any]],
    user_content: str,
    tool: dict[str, Any],
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> dict[str, Any]:
    """Force a single structured tool call and return its input dict.

    ``system_blocks`` is a list of content blocks (so the caller can mark the
    rubric library and transcript as cache_control: ephemeral). The judge is
    forced to emit the verdict via tool_choice, which guarantees schema shape.
    """
    client = _client()

    def call():
        return client.messages.create(
            model=model,
            system=system_blocks,
            messages=[{"role": "user", "content": user_content}],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            max_tokens=max_tokens,
            temperature=temperature,
        )

    resp = _with_retry(call, what=f"verdict[{model}]")
    for block in resp.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return dict(block.input)
    raise TargetError(f"judge {model} returned no tool call")
