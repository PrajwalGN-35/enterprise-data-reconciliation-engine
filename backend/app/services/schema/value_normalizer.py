from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd


MISSING_VALUE_MARKERS = {
    "",
    "na",
    "n/a",
    "nan",
    "null",
    "none",
    "nil",
}


def normalize_text_value(value: Any) -> Any:
    """
    Normalize text-like values without changing their
    underlying meaning.

    Non-string values are returned unchanged.
    """
    if not isinstance(value, str):
        return value

    normalized = value.strip()

    if normalized.lower() in MISSING_VALUE_MARKERS:
        return None

    return normalized.lower()


def normalize_numeric_value(value: Any) -> Any:
    """
    Normalize numeric-looking values into Decimal.

    Missing values become None. Non-numeric values are returned unchanged.
    """
    if value is None or isinstance(value, bool):
        return value

    if pd.isna(value):
        return None

    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return value

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")

        if cleaned.lower() in MISSING_VALUE_MARKERS:
            return None

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return value

    return value


def normalize_date_value(value: Any) -> Any:
    """
    Normalize recognizable date/datetime values into ISO format.

    Unrecognized values are returned unchanged.
    """
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, str):
        cleaned = value.strip()

        if cleaned.lower() in MISSING_VALUE_MARKERS:
            return None

        parsed = pd.to_datetime(
            cleaned,
            errors="coerce",
            dayfirst=False,
        )

        if pd.notna(parsed):
            return parsed.strftime("%Y-%m-%d")

    return value
