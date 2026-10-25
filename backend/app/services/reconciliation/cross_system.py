"""Cross-system dataset boundary for the reconciliation workflow."""

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.services.reconciliation.orchestrator import (
    ReconciliationWorkflowResult,
    run_reconciliation_workflow,
)
from app.services.schema.normalizer import normalize_column_name


class CrossSystemIntegrationError(ValueError):
    """Raised when a supplied cross-system dataset is not usable."""


@dataclass(frozen=True)
class CrossSystemDataset:
    """A supplied system dataset and its canonical field contract."""

    system_name: str
    dataset_name: str
    dataframe: pd.DataFrame
    field_mapping: dict[str, str] | None = None
    record_id_field: str | None = None


@dataclass(frozen=True)
class CrossSystemRecordReference:
    """Traceability metadata for one normalized workflow record."""

    role: str
    system_name: str
    dataset_name: str
    record_index: int
    record_id: Any


@dataclass(frozen=True)
class CrossSystemWorkflowResult:
    """Workflow output with system metadata and record traceability."""

    source: CrossSystemDataset
    target: CrossSystemDataset
    workflow: ReconciliationWorkflowResult
    source_records: tuple[CrossSystemRecordReference, ...]
    target_records: tuple[CrossSystemRecordReference, ...]


def _validate_name(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CrossSystemIntegrationError(
            f"{label} must be a non-empty string."
        )


def _mapped_dataframe(dataset: CrossSystemDataset) -> pd.DataFrame:
    _validate_name(dataset.system_name, "system_name")
    _validate_name(dataset.dataset_name, "dataset_name")

    if not isinstance(dataset.dataframe, pd.DataFrame):
        raise CrossSystemIntegrationError(
            "dataframe must be a pandas DataFrame."
        )

    if any(
        not isinstance(column, str)
        for column in dataset.dataframe.columns
    ):
        raise CrossSystemIntegrationError(
            "All dataframe column labels must be strings."
        )

    mapping = dataset.field_mapping
    if mapping is None:
        mapping = {}
    if not isinstance(mapping, dict):
        raise CrossSystemIntegrationError(
            "field_mapping must be a dictionary."
        )

    renamed_columns: dict[str, str] = {}
    for source_column, canonical_column in mapping.items():
        if not isinstance(source_column, str) or not source_column.strip():
            raise CrossSystemIntegrationError(
                "field_mapping source names must be non-empty strings."
            )
        if not isinstance(canonical_column, str) or not canonical_column.strip():
            raise CrossSystemIntegrationError(
                "field_mapping canonical names must be non-empty strings."
            )
        renamed_columns[source_column] = canonical_column

    dataframe = dataset.dataframe.copy()
    missing_mapping_columns = [
        column
        for column in renamed_columns
        if column not in dataframe.columns
    ]
    if missing_mapping_columns:
        raise CrossSystemIntegrationError(
            "Mapped source columns are missing from "
            f"{dataset.system_name}/{dataset.dataset_name}: "
            f"{missing_mapping_columns}"
        )

    dataframe = dataframe.rename(columns=renamed_columns)
    normalized_columns = [normalize_column_name(column) for column in dataframe.columns]
    if len(normalized_columns) != len(set(normalized_columns)):
        raise CrossSystemIntegrationError(
            "Field mapping produces duplicate normalized columns for "
            f"{dataset.system_name}/{dataset.dataset_name}."
        )

    dataframe.columns = normalized_columns
    return dataframe


def _validate_workflow_inputs(
    source_dataframe: pd.DataFrame,
    target_dataframe: pd.DataFrame,
    matching_fields: list[str],
    reconciliation_fields: list[str],
    workflow_kwargs: dict[str, Any],
) -> None:
    if not matching_fields:
        raise CrossSystemIntegrationError(
            "At least one matching field is required."
        )
    if not reconciliation_fields:
        raise CrossSystemIntegrationError(
            "At least one reconciliation field is required."
        )

    for field_group, fields in (
        ("matching", matching_fields),
        ("reconciliation", reconciliation_fields),
    ):
        for dataframe, label in (
            (source_dataframe, "source"),
            (target_dataframe, "target"),
        ):
            missing_fields = [
                field for field in fields if field not in dataframe.columns
            ]
            if missing_fields:
                raise CrossSystemIntegrationError(
                    f"Missing {field_group} fields: {missing_fields}"
                )

    high_confidence_threshold = workflow_kwargs.get(
        "high_confidence_threshold",
        0.90,
    )
    review_threshold = workflow_kwargs.get("review_threshold", 0.75)
    ambiguity_margin = workflow_kwargs.get("ambiguity_margin", 0.05)
    try:
        thresholds_valid = (
            0 <= review_threshold <= high_confidence_threshold <= 1
        )
        margin_valid = 0 <= ambiguity_margin <= 1
    except TypeError as exc:
        raise CrossSystemIntegrationError(
            "Matching thresholds and ambiguity margin must be numbers."
        ) from exc

    if not thresholds_valid:
        raise CrossSystemIntegrationError(
            "Thresholds must satisfy "
            "0 <= review_threshold <= high_confidence_threshold <= 1."
        )
    if not margin_valid:
        raise CrossSystemIntegrationError(
            "Ambiguity margin must be between 0 and 1."
        )


def _record_references(
    dataset: CrossSystemDataset,
    dataframe: pd.DataFrame,
    role: str,
) -> tuple[CrossSystemRecordReference, ...]:
    if dataset.record_id_field is None:
        return tuple(
            CrossSystemRecordReference(
                role=role,
                system_name=dataset.system_name,
                dataset_name=dataset.dataset_name,
                record_index=index,
                record_id=None,
            )
            for index in range(len(dataframe))
        )

    _validate_name(dataset.record_id_field, "record_id_field")
    normalized_id_field = normalize_column_name(
        (dataset.field_mapping or {}).get(
            dataset.record_id_field,
            dataset.record_id_field,
        )
    )
    if normalized_id_field not in dataframe.columns:
        raise CrossSystemIntegrationError(
            f"Record identifier field '{dataset.record_id_field}' is not "
            f"available in {dataset.system_name}/{dataset.dataset_name}."
        )

    return tuple(
        CrossSystemRecordReference(
            role=role,
            system_name=dataset.system_name,
            dataset_name=dataset.dataset_name,
            record_index=index,
            record_id=dataframe.iloc[index][normalized_id_field],
        )
        for index in range(len(dataframe))
    )


def run_cross_system_reconciliation(
    source: CrossSystemDataset,
    target: CrossSystemDataset,
    matching_fields: list[str],
    reconciliation_fields: list[str],
    **workflow_kwargs: Any,
) -> CrossSystemWorkflowResult:
    """Map two supplied system datasets into the existing workflow."""

    source_dataframe = _mapped_dataframe(source)
    target_dataframe = _mapped_dataframe(target)

    _validate_workflow_inputs(
        source_dataframe,
        target_dataframe,
        matching_fields,
        reconciliation_fields,
        workflow_kwargs,
    )

    workflow = run_reconciliation_workflow(
        source_dataframe=source_dataframe,
        target_dataframe=target_dataframe,
        matching_fields=matching_fields,
        reconciliation_fields=reconciliation_fields,
        **workflow_kwargs,
    )

    return CrossSystemWorkflowResult(
        source=source,
        target=target,
        workflow=workflow,
        source_records=_record_references(
            source,
            source_dataframe,
            "source",
        ),
        target_records=_record_references(
            target,
            target_dataframe,
            "target",
        ),
    )