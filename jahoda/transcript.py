"""Conversation transcript models — the unit a fresh-context judge reads."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from jahoda.schemas import SessionMetadata


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Transcript(BaseModel):
    """One full multi-turn run of a scenario against a target."""

    scenario_id: str
    dimension: str
    target_id: str
    subject_model: str | None = None
    run_index: int
    session_metadata: SessionMetadata | None = None
    messages: list[Message] = Field(default_factory=list)
    target_error: str | None = None

    def assistant_text(self) -> str:
        """All assistant turns concatenated — the surface a quote must match."""
        return "\n".join(m.content for m in self.messages if m.role == "assistant")

    def render(self) -> str:
        """Human/judge-readable rendering with turn labels."""
        lines: list[str] = []
        if self.session_metadata:
            sm = self.session_metadata
            bits = []
            if sm.message_count is not None:
                bits.append(f"message {sm.message_count}")
            if sm.elapsed_minutes is not None:
                bits.append(f"{sm.elapsed_minutes} min elapsed")
            if sm.local_hour is not None:
                bits.append(f"local hour {sm.local_hour:02d}:00")
            if sm.suspected_minor:
                bits.append("suspected minor")
            if bits:
                lines.append(f"[session: {', '.join(bits)}]")
        for m in self.messages:
            who = "USER" if m.role == "user" else "GUIDE"
            lines.append(f"{who}: {m.content}")
        return "\n".join(lines)
