import math
import unicodedata
from typing import Any

import numpy as np
import pandas as pd
from rapidfuzz import fuzz


_MISSING_TEXT_VALUES = {
    "",
    "na",
    "n/a",
    "nan",
    "null",
    "none",
    "nil",
}


def normalize_for_similarity(value: Any) -> str:
    """Convert a value into a stable fuzzy-matching representation."""
    missing = pd.isna(value)

    if isinstance(missing, (bool, np.bool_)) and bool(missing):
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = " ".join(text.split()).casefold()
    text = unicodedata.normalize("NFC", text)

    if text in _MISSING_TEXT_VALUES:
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

    score = fuzz.WRatio(source, target) / 100

    if not math.isfinite(score):
        return 0.0

    return round(min(max(score, 0.0), 1.0), 4)
