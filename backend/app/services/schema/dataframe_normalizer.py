from typing import Any

import pandas as pd

from app.services.schema.value_normalizer import (
    normalize_date_value,
    normalize_numeric_value,
    normalize_text_value,
)


def normalize_identifier_value(value: Any) -> Any:
    """
    Normalize identifier-like values without changing their case.

    Identifiers may be case-sensitive, so only surrounding
    whitespace and recognized missing markers are removed.
    """
    if value is None:
        return None

    if pd.isna(value):
        return None

    if not isinstance(value, str):
        return value

    normalized = value.strip()

    if normalized.lower() in {
        "",
        "na",
        "n/a",
        "nan",
        "null",
        "none",
        "nil",
    }:
        return None

    return normalized


def _apply_normalizer(
    series: pd.Series,
    normalizer,
) -> pd.Series:
    """
    Apply a value normalizer while retaining object dtype.
    """
    return pd.Series(
        [normalizer(value) for value in series.tolist()],
        index=series.index,
        dtype=object,
    )


def normalize_dataframe_values(
    dataframe: pd.DataFrame,
    column_types: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Normalize dataframe values according to explicit column types.

    Supported types:
        text
        identifier
        numeric
        date

    Columns without an explicit type default to text normalization.
    """
    normalized_dataframe = dataframe.copy()
    column_types = column_types or {}

    supported_types = {
        "text",
        "identifier",
        "numeric",
        "date",
    }

    for column in normalized_dataframe.columns:
        column_type = column_types.get(column, "text")

        if column_type not in supported_types:
            raise ValueError(
                f"Unsupported normalization type '{column_type}' "
                f"for column '{column}'. "
                f"Supported types: {sorted(supported_types)}"
            )

        if column_type == "identifier":
            normalizer = normalize_identifier_value
        elif column_type == "numeric":
            normalizer = normalize_numeric_value
        elif column_type == "date":
            normalizer = normalize_date_value
        else:
            normalizer = normalize_text_value

        normalized_dataframe[column] = _apply_normalizer(
            normalized_dataframe[column],
            normalizer,
        )

    return normalized_dataframe
