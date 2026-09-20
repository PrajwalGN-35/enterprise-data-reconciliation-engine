from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.services.matching.entity_matcher import match_entities
from app.services.reconciliation.reconciler import (
    ReconciliationResult,
    reconcile_matches,
)
from app.services.reconciliation.summary import (
    ReconciliationSummary,
    summarize_reconciliation,
)
from app.services.schema.dataframe_normalizer import (
    normalize_dataframe_values,
)
from app.services.schema.matcher import compare_schemas
from app.services.schema.transformer import (
    normalize_dataframe_columns,
)


@dataclass
class ReconciliationWorkflowResult:
    schema_comparison: dict
    matches: list[Any]
    reconciliation_results: list[ReconciliationResult]
    summary: ReconciliationSummary


def _records_from_dataframe(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a normalized dataframe into reconciliation records."""
    return dataframe.to_dict(orient="records")


def _validate_fields(
    dataframe: pd.DataFrame,
    fields: list[str],
    field_group: str,
) -> None:
    missing_fields = [
        field
        for field in fields
        if field not in dataframe.columns
    ]

    if missing_fields:
        raise ValueError(
            f"Missing {field_group} fields: {missing_fields}"
        )


def run_reconciliation_workflow(
    source_dataframe: pd.DataFrame,
    target_dataframe: pd.DataFrame,
    matching_fields: list[str],
    reconciliation_fields: list[str],
    column_types: dict[str, str] | None = None,
    high_confidence_threshold: float = 0.90,
    review_threshold: float = 0.75,
    ambiguity_margin: float = 0.05,
) -> ReconciliationWorkflowResult:
    """
    Execute the complete in-memory reconciliation workflow.

    Workflow:
        1. Compare source and target schemas using original column names.
        2. Normalize column names for downstream processing.
        3. Normalize dataset values.
        4. Match source entities to target entities.
        5. Reconcile configured fields.
        6. Build aggregate reconciliation metrics.

    The function does not persist data or perform file I/O.
    """

    if not matching_fields:
        raise ValueError(
            "At least one matching field is required."
        )

    if not reconciliation_fields:
        raise ValueError(
            "At least one reconciliation field is required."
        )

    schema_comparison = compare_schemas(
        list(source_dataframe.columns),
        list(target_dataframe.columns),
    )

    source_normalized = normalize_dataframe_columns(
        source_dataframe
    )
    target_normalized = normalize_dataframe_columns(
        target_dataframe
    )

    _validate_fields(
        source_normalized,
        matching_fields,
        "matching",
    )
    _validate_fields(
        target_normalized,
        matching_fields,
        "matching",
    )
    _validate_fields(
        source_normalized,
        reconciliation_fields,
        "reconciliation",
    )
    _validate_fields(
        target_normalized,
        reconciliation_fields,
        "reconciliation",
    )

    normalized_source = normalize_dataframe_values(
        source_normalized,
        column_types,
    )
    normalized_target = normalize_dataframe_values(
        target_normalized,
        column_types,
    )

    source_records = _records_from_dataframe(
        normalized_source
    )
    target_records = _records_from_dataframe(
        normalized_target
    )

    matches = match_entities(
        source_records=source_records,
        target_records=target_records,
        fields=matching_fields,
        high_confidence_threshold=high_confidence_threshold,
        review_threshold=review_threshold,
        ambiguity_margin=ambiguity_margin,
    )

    reconciliation_results = reconcile_matches(
        source_records=source_records,
        target_records=target_records,
        matches=matches,
        fields=reconciliation_fields,
    )

    summary = summarize_reconciliation(
        results=reconciliation_results,
        source_record_count=len(source_records),
        target_record_count=len(target_records),
    )

    return ReconciliationWorkflowResult(
        schema_comparison=schema_comparison,
        matches=matches,
        reconciliation_results=reconciliation_results,
        summary=summary,
    )

