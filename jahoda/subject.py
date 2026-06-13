"""Specimen (sketch-BRUJAI) and vanilla-baseline target construction.

The specimen is a minimal demo target: persona voice + a guardrail layer, on
the Anthropic API. The vanilla baseline is a frontier model behind ONE neutral
generic sentence and is served over HTTP (see vanilla_server.py) so it is a
structurally different target, not a config flag on the same path.
"""

from __future__ import annotations

from pathlib import Path

from jahoda.config import MODELS
from jahoda.targets import AnthropicTarget

SUBJECT_DIR = Path(__file__).resolve().parent.parent / "subject"

SPECIMEN_ID = "sketch-brujai"
VANILLA_ID = "vanilla-baseline"


def specimen_system_prompt() -> str:
    persona = (SUBJECT_DIR / "persona.md").read_text().strip()
    guardrails = (SUBJECT_DIR / "guardrails.md").read_text().strip()
    return f"{persona}\n\n---\n\n{guardrails}"


def vanilla_prompt() -> str:
    return (SUBJECT_DIR / "vanilla_prompt.txt").read_text().strip()


def build_specimen_target(model: str | None = None) -> AnthropicTarget:
    return AnthropicTarget(
        target_id=SPECIMEN_ID,
        model=model or MODELS.subject,
        system_prompt=specimen_system_prompt(),
        audience="all-ages",
    )


def build_vanilla_anthropic_target(model: str | None = None) -> AnthropicTarget:
    """Direct-mode vanilla (used by the HTTP wrapper and as a fallback)."""
    return AnthropicTarget(
        target_id=VANILLA_ID,
        model=model or MODELS.subject,
        system_prompt=vanilla_prompt(),
        audience="adult-only",
    )
