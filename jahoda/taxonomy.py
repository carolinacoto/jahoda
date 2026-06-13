"""Feeling Wheel taxonomy loader (Willcox 1982).

The verifier classifies expressed emotion at the six-core-category level using
this file, not ad-hoc labels (rubric B3). Vocabulary, not a validated
instrument — see verifier/taxonomy/feeling_wheel.yaml.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

TAXONOMY_PATH = (
    Path(__file__).resolve().parent.parent / "verifier" / "taxonomy" / "feeling_wheel.yaml"
)


@lru_cache(maxsize=1)
def load_feeling_wheel() -> dict:
    return yaml.safe_load(TAXONOMY_PATH.read_text())


def core_categories() -> list[str]:
    return list(load_feeling_wheel()["core"].keys())


def judge_emotion_hint() -> str:
    """One line injected into judges so emotion attunement uses the 6 categories."""
    cats = ", ".join(core_categories())
    return (
        "When a criterion concerns emotional attunement, classify the emotion the "
        f"user actually expressed at the Feeling Wheel (Willcox 1982) six-core level "
        f"[{cats}] — not a generic flattened version."
    )
