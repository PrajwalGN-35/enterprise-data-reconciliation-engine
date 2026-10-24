from dataclasses import dataclass
from math import isfinite
from numbers import Real

from .reconciler import ReconciliationResult


_STATUSES = {"matched", "discrepancy", "missing_target", "review_required"}
_PRIORITIES = ("critical", "high", "medium", "low")


def _validate_weight(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite non-negative number.")
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number.")


@dataclass(frozen=True)
class DiscrepancyImpactConfig:
    field_weights: dict[str, float] | None = None
    default_field_weight: float = 1.0
    discrepancy_weight: float = 0.5
    missing_target_weight: float = 1.0
    review_required_weight: float = 0.75
    critical_threshold: float = 0.8
    high_threshold: float = 0.6
    medium_threshold: float = 0.3

    def __post_init__(self) -> None:
        _validate_weight("default_field_weight", self.default_field_weight)
        _validate_weight("discrepancy_weight", self.discrepancy_weight)
        _validate_weight("missing_target_weight", self.missing_target_weight)
        _validate_weight("review_required_weight", self.review_required_weight)

        for field, weight in (self.field_weights or {}).items():
            if not isinstance(field, str) or not field.strip():
                raise ValueError("field_weights must use non-empty field names.")
            _validate_weight(f"field_weights[{field!r}]", weight)

        thresholds = (
            self.critical_threshold,
            self.high_threshold,
            self.medium_threshold,
        )
        if any(
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not isfinite(value)
            or not 0 <= value <= 1
            for value in thresholds
        ):
            raise ValueError("Impact thresholds must be finite numbers between 0 and 1.")
        if not self.critical_threshold > self.high_threshold > self.medium_threshold:
            raise ValueError("Impact thresholds must be strictly descending.")

        if not any(
            weight > 0
            for weight in (self.field_weights or {}).values()
        ) and self.default_field_weight == 0:
            raise ValueError("At least one field weight must be greater than zero.")


@dataclass(frozen=True)
class DiscrepancyImpactAssessment:
    source_index: int
    target_index: int | None
    status: str
    impact_score: float
    priority: str
    reason_codes: tuple[str, ...]
    discrepant_fields: tuple[str, ...]


@dataclass(frozen=True)
class DiscrepancyImpactAnalysis:
    source_record_count: int
    affected_record_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_impact_score: float
    exceptions: tuple[DiscrepancyImpactAssessment, ...]


def _priority(score: float, config: DiscrepancyImpactConfig) -> str:
    if score >= config.critical_threshold:
        return "critical"
    if score >= config.high_threshold:
        return "high"
    if score >= config.medium_threshold:
        return "medium"
    return "low"


def _field_weight(field: str, config: DiscrepancyImpactConfig) -> float:
    return (config.field_weights or {}).get(field, config.default_field_weight)


def _assessment(
    result: ReconciliationResult,
    config: DiscrepancyImpactConfig,
) -> DiscrepancyImpactAssessment | None:
    if result.status not in _STATUSES:
        raise ValueError(f"Unsupported reconciliation status: '{result.status}'.")
    if result.status == "matched":
        return None

    discrepant_fields = tuple(
        dict.fromkeys(discrepancy.field for discrepancy in result.discrepancies)
    )
    baseline = {
        "discrepancy": config.discrepancy_weight,
        "missing_target": config.missing_target_weight,
        "review_required": config.review_required_weight,
    }.get(result.status, 0.0)
    score = baseline
    reason_codes = [f"status_{result.status}"]

    if result.status == "discrepancy":
        compared_fields = tuple(
            dict.fromkeys(result.compared_fields or discrepant_fields)
        )
        if result.compared_fields and not set(discrepant_fields).issubset(compared_fields):
            raise ValueError("Discrepant fields must be included in compared_fields.")
        denominator = sum(
            _field_weight(field, config) for field in compared_fields
        )
        if denominator <= 0:
            raise ValueError("Compared fields must have a positive total weight.")
        field_coverage = sum(
            _field_weight(field, config) for field in discrepant_fields
        ) / denominator
        score = max(score, field_coverage)
        reason_codes.append("weighted_field_coverage")

    bounded_score = round(min(max(score, 0.0), 1.0), 4)
    priority = _priority(bounded_score, config)
    reason_codes.append(f"priority_{priority}")

    return DiscrepancyImpactAssessment(
        source_index=result.source_index,
        target_index=result.target_index,
        status=result.status,
        impact_score=bounded_score,
        priority=priority,
        reason_codes=tuple(reason_codes),
        discrepant_fields=discrepant_fields,
    )


def analyze_reconciliation_impact(
    results: list[ReconciliationResult],
    source_record_count: int,
    config: DiscrepancyImpactConfig | None = None,
) -> DiscrepancyImpactAnalysis:
    if (
        isinstance(source_record_count, bool)
        or not isinstance(source_record_count, int)
        or source_record_count < 0
    ):
        raise ValueError("source_record_count must be a non-negative integer.")
    if len(results) != source_record_count:
        raise ValueError(
            "Impact results must contain exactly one result for each source record."
        )

    source_indices = [result.source_index for result in results]
    if any(
        isinstance(index, bool)
        or not isinstance(index, int)
        or index < 0
        or index >= source_record_count
        for index in source_indices
    ):
        raise ValueError("Each source_index must be an integer within the source record range.")
    if len(set(source_indices)) != len(source_indices):
        raise ValueError("Each source record must have a unique source_index.")

    config = config or DiscrepancyImpactConfig()
    assessments = tuple(
        assessment
        for result in results
        for assessment in [_assessment(result, config)]
        if assessment is not None
    )
    assessments = tuple(
        sorted(
            assessments,
            key=lambda item: (-item.impact_score, item.source_index),
        )
    )
    counts = {
        priority: sum(item.priority == priority for item in assessments)
        for priority in _PRIORITIES
    }

    return DiscrepancyImpactAnalysis(
        source_record_count=source_record_count,
        affected_record_count=len(assessments),
        critical_count=counts["critical"],
        high_count=counts["high"],
        medium_count=counts["medium"],
        low_count=counts["low"],
        total_impact_score=round(
            sum(item.impact_score for item in assessments),
            4,
        ),
        exceptions=assessments,
    )