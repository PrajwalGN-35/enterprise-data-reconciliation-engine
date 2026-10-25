"""Cross-system report generation, serialization, and persistence."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
import json
import math
from numbers import Real
import uuid
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models import AuditLog, CrossSystemReport
from app.services.reconciliation.cross_system import (
    CrossSystemIntegrationError,
    CrossSystemWorkflowResult,
)


REPORT_SCHEMA_VERSION = "7.9.1"


class CrossSystemReportError(ValueError):
    """Raised when a report cannot be generated or safely stored."""


class CrossSystemReportPayloadError(CrossSystemReportError):
    """Raised when persisted report content is corrupted."""


def _json_value(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, Enum):
        return _json_value(value.value)

    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    if isinstance(value, uuid.UUID):
        return str(value)

    if isinstance(value, np.generic):
        return _json_value(value.item())

    if isinstance(value, Decimal):
        converted = float(value)
        if not math.isfinite(converted):
            raise TypeError("Non-finite Decimal values are not supported.")
        return converted

    if isinstance(value, Real) and not isinstance(value, bool):
        converted = float(value) if isinstance(value, float) else value
        if isinstance(converted, float) and not math.isfinite(converted):
            raise TypeError("Non-finite numeric values are not supported.")
        return converted

    if isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise TypeError("Non-finite numeric values are not supported.")
        return value

    if is_dataclass(value):
        return {
            item.name: _json_value(getattr(value, item.name))
            for item in fields(value)
        }

    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("Report dictionaries must use string keys.")
        return {key: _json_value(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]

    raise TypeError(
        f"Unsupported report value type: {type(value).__name__}."
    )


def serialize_report_value(value: Any) -> Any:
    """Return a strict JSON-compatible representation of a supported value."""
    normalized = _json_value(value)
    json.dumps(normalized, allow_nan=False)
    return normalized


def _reference_payload(reference: Any) -> dict[str, Any]:
    return serialize_report_value(reference)


def _validate_workflow_result(result: CrossSystemWorkflowResult) -> None:
    workflow = result.workflow
    if len(workflow.matches) != len(result.source_records):
        raise CrossSystemReportError(
            "Match count must equal source reference count."
        )
    if len(workflow.reconciliation_results) != len(result.source_records):
        raise CrossSystemReportError(
            "Reconciliation count must equal source reference count."
        )

    for index, reference in enumerate(result.source_records):
        if reference.role != "source" or reference.record_index != index:
            raise CrossSystemReportError(
                "Source references must preserve zero-based workflow order."
            )

    for index, reference in enumerate(result.target_records):
        if reference.role != "target" or reference.record_index != index:
            raise CrossSystemReportError(
                "Target references must preserve zero-based workflow order."
            )

    target_count = len(result.target_records)
    for index, match in enumerate(workflow.matches):
        if match.source_index != index:
            raise CrossSystemReportError(
                "Match source_index does not align with source references."
            )
        if match.target_index is not None and not (
            isinstance(match.target_index, int)
            and 0 <= match.target_index < target_count
        ):
            raise CrossSystemReportError(
                "Match target_index does not align with target references."
            )

    for index, reconciliation in enumerate(workflow.reconciliation_results):
        if reconciliation.source_index != index:
            raise CrossSystemReportError(
                "Reconciliation source_index does not align with sources."
            )
        if reconciliation.target_index is not None and not (
            isinstance(reconciliation.target_index, int)
            and 0 <= reconciliation.target_index < target_count
        ):
            raise CrossSystemReportError(
                "Reconciliation target_index is out of bounds."
            )


def build_cross_system_report(
    result: CrossSystemWorkflowResult,
    *,
    report_id: str,
    generated_at: datetime | None = None,
    execution_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a versioned report from an actual cross-system workflow result."""
    if not isinstance(result, CrossSystemWorkflowResult):
        raise CrossSystemReportError(
            "result must be a CrossSystemWorkflowResult."
        )
    try:
        report_uuid = str(uuid.UUID(report_id))
    except (ValueError, AttributeError, TypeError) as exc:
        raise CrossSystemReportError("report_id must be a valid UUID.") from exc

    _validate_workflow_result(result)
    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    outcomes = []
    for match, reconciliation in zip(
        result.workflow.matches,
        result.workflow.reconciliation_results,
    ):
        target_reference = (
            result.target_records[match.target_index]
            if match.target_index is not None
            else None
        )
        outcomes.append(
            {
                "source_reference": _reference_payload(
                    result.source_records[match.source_index]
                ),
                "target_reference": (
                    _reference_payload(target_reference)
                    if target_reference is not None
                    else None
                ),
                "match": serialize_report_value(match),
                "reconciliation": serialize_report_value(reconciliation),
            }
        )

    payload: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": report_uuid,
        "generated_at": timestamp.isoformat(),
        "source": {
            "system_name": result.source.system_name,
            "dataset_name": result.source.dataset_name,
        },
        "target": {
            "system_name": result.target.system_name,
            "dataset_name": result.target.dataset_name,
        },
        "schema_comparison": serialize_report_value(
            result.workflow.schema_comparison
        ),
        "summary": serialize_report_value(result.workflow.summary),
        "impact_analysis": serialize_report_value(
            result.workflow.impact_analysis
        ),
        "source_records": [
            _reference_payload(reference)
            for reference in result.source_records
        ],
        "target_records": [
            _reference_payload(reference)
            for reference in result.target_records
        ],
        "outcomes": outcomes,
        "counts": {
            "source_records": len(result.source_records),
            "target_records": len(result.target_records),
            "outcomes": len(outcomes),
        },
    }
    if execution_metadata is not None:
        payload["execution_metadata"] = serialize_report_value(
            execution_metadata
        )

    serialize_report_value(payload)
    return payload


def persist_cross_system_report(
    db: Session,
    result: CrossSystemWorkflowResult,
    *,
    execution_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a report and its success audit event in one transaction."""
    report_id = str(uuid.uuid4())
    payload = build_cross_system_report(
        result,
        report_id=report_id,
        execution_metadata=execution_metadata,
    )
    serialized_payload = json.dumps(payload, allow_nan=False)
    report = CrossSystemReport(
        id=report_id,
        schema_version=REPORT_SCHEMA_VERSION,
        source_system=result.source.system_name,
        source_dataset=result.source.dataset_name,
        target_system=result.target.system_name,
        target_dataset=result.target.dataset_name,
        status="persisted",
        payload=serialized_payload,
    )
    audit = AuditLog(
        action="cross_system_report_persisted",
        entity_type="cross_system_report",
        entity_id=report_id,
        details=json.dumps(
            {
                "report_id": report_id,
                "schema_version": REPORT_SCHEMA_VERSION,
                "source_system": result.source.system_name,
                "source_dataset": result.source.dataset_name,
                "target_system": result.target.system_name,
                "target_dataset": result.target.dataset_name,
            },
            allow_nan=False,
        ),
    )
    try:
        db.add(report)
        db.add(audit)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return payload


def retrieve_cross_system_report(
    db: Session,
    report_id: str,
) -> dict[str, Any] | None:
    """Retrieve and strictly decode a persisted report payload."""
    try:
        normalized_id = str(uuid.UUID(report_id))
    except (ValueError, AttributeError, TypeError) as exc:
        raise CrossSystemReportError("report_id must be a valid UUID.") from exc

    report = db.get(CrossSystemReport, normalized_id)
    if report is None:
        return None
    try:
        payload = json.loads(report.payload)
        serialize_report_value(payload)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CrossSystemReportPayloadError(
            "Persisted cross-system report payload is invalid."
        ) from exc
    return payload
