from typing import Any

from rapidfuzz import fuzz


def normalize_for_similarity(value: Any) -> str:
    """Convert a value into a stable fuzzy-matching representation."""
    if value is None:
        return ""

    text = str(value).strip().lower()

    if text in {"", "na", "n/a", "nan", "null", "none", "nil"}:
        return ""

    return text


def calculate_similarity(
    source_value: Any,
    target_value: Any,
) -> float:
    """Return a fuzzy similarity score between 0 and 1."""
    source = normalize_for_similarity(source_value)
    target = normalize_for_similarity(target_value)

    if not source or not target:
        return 0.0

    if source == target:
        return 1.0

    return round(
        fuzz.WRatio(source, target) / 100,
        4,
    )
