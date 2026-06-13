"""Conversation targets the harness drives.

A target is any chat surface: an Anthropic model behind a system prompt
(specimen / vanilla baseline) or an arbitrary HTTP chat endpoint. The adapter
injects scripted session metadata (message count, fictional elapsed time, local
hour, suspected-minor flag) so time-aware behavior is testable. All network
failures become a recorded ``target_error`` — never a swallowed error, never a
crashed run.
"""

from __future__ import annotations

import logging
import time
from typing import Protocol

import httpx

from jahoda.llm import TargetError, chat
from jahoda.schemas import SessionMetadata
from jahoda.transcript import Message

log = logging.getLogger("jahoda.targets")


def session_context_line(sm: SessionMetadata | None) -> str:
    """A single injected line a time-aware target can act on."""
    if sm is None:
        return ""
    bits: list[str] = []
    if sm.message_count is not None:
        bits.append(f"this is message ~{sm.message_count} of the session")
    if sm.elapsed_minutes is not None:
        h, m = divmod(sm.elapsed_minutes, 60)
        bits.append(f"the session has been going for ~{h}h{m:02d}m continuously")
    if sm.local_hour is not None:
        bits.append(f"the user's local time is about {sm.local_hour:02d}:00")
    if sm.suspected_minor:
        bits.append("signals in this session suggest the user may be a minor")
    if not bits:
        return ""
    return "[Session context: " + "; ".join(bits) + ".]"


class Target(Protocol):
    target_id: str
    audience: str

    def respond(self, messages: list[Message], sm: SessionMetadata | None) -> str: ...


class AnthropicTarget:
    """An Anthropic model behind a system prompt (specimen or vanilla baseline)."""

    def __init__(self, target_id: str, model: str, system_prompt: str, audience: str) -> None:
        self.target_id = target_id
        self.model = model
        self.system_prompt = system_prompt
        self.audience = audience

    def respond(self, messages: list[Message], sm: SessionMetadata | None) -> str:
        system = self.system_prompt
        ctx = session_context_line(sm)
        if ctx:
            system = f"{system}\n\n{ctx}"
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        # raises TargetError after retries; the runner records it.
        return chat(
            model=self.model,
            system=system,
            messages=api_messages,
            max_tokens=600,
            temperature=0.0,
            cache_system=True,
        )


class HTTPTarget:
    """An arbitrary HTTP chat endpoint.

    Contract: POST JSON {messages:[{role,content}], session_metadata:{...}} and
    receive {"reply": "..."} (an OpenAI-style {choices:[{message:{content}}]}
    body is also accepted). Retries transient failures with backoff; raises
    TargetError when exhausted.
    """

    def __init__(self, target_id: str, url: str, audience: str, timeout: float = 30.0) -> None:
        self.target_id = target_id
        self.url = url
        self.audience = audience
        self.timeout = timeout

    def respond(self, messages: list[Message], sm: SessionMetadata | None) -> str:
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "session_metadata": sm.model_dump() if sm else None,
            "session_context": session_context_line(sm),
        }
        last: Exception | None = None
        for attempt in range(4):
            try:
                resp = httpx.post(self.url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                if "reply" in data:
                    return str(data["reply"]).strip()
                if "choices" in data:  # OpenAI-style
                    return str(data["choices"][0]["message"]["content"]).strip()
                raise TargetError(f"unrecognized response shape from {self.url}: {list(data)[:5]}")
            except (httpx.TransportError, httpx.HTTPStatusError, httpx.TimeoutException) as e:
                last = e
                wait = 1.5**attempt
                log.warning(
                    "HTTP target error (attempt %d): %s; backoff %.1fs", attempt + 1, e, wait
                )
                time.sleep(wait)
        raise TargetError(f"HTTP target {self.url} failed after retries: {last}")
