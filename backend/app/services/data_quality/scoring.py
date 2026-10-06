from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .engine import (
    DatasetQualityReport,
    QualitySeverity,
)


class QualityRisk(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class QualityScoringConfig:
    info_weight: float = 0.05
    warning_weight: float = 0.10
    error_weight: float = 0.20
    critical_weight: float = 0.40

    excellent_threshold: float = 95.0
    good_threshold: float = 85.0
    fair_threshold: float = 70.0
    poor_threshold: float = 50.0

    def __post_init__(self) -> None:
        weights = (
            self.info_weight,
            self.warning_weight,
            self.error_weight,
            self.critical_weight,
        )

        if any(weight < 0 for weight in weights):
            raise ValueError("Severity weights must not be negative.")

        thresholds = (
            self.excellent_threshold,
            self.good_threshold,
            self.fair_threshold,
            self.poor_threshold,
        )

        if any(
            threshold < 0 or threshold > 100
            for threshold in thresholds
        ):
            raise ValueError(
                "Risk thresholds must be between 0 and 100."
            )

        if not (
            self.excellent_threshold
            > self.good_threshold
            > self.fair_threshold
            > self.poor_threshold
        ):
            raise ValueError(
                "Risk thresholds must be strictly descending."
            )


@dataclass(frozen=True)
class QualityRuleScore:
    rule_name: str
    score: float
    impact: float
    issue_count: int
    affected_rows: int


@dataclass(frozen=True)
class QualityScore:
    dataset: str
    score: float
    risk: QualityRisk
    rule_scores: tuple[QualityRuleScore, ...]

    @property
    def rule_count(self) -> int:
        return len(self.rule_scores)

    @property
    def failed_rule_count(self) -> int:
        return sum(
            1
            for rule_score in self.rule_scores
            if rule_score.issue_count > 0
        )


def _severity_weight(
    severity: QualitySeverity,
    config: QualityScoringConfig,
) -> float:
    weights = {
        QualitySeverity.INFO: config.info_weight,
        QualitySeverity.WARNING: config.warning_weight,
        QualitySeverity.ERROR: config.error_weight,
        QualitySeverity.CRITICAL: config.critical_weight,
    }

    return weights[severity]


def _risk_from_score(
    score: float,
    config: QualityScoringConfig,
) -> QualityRisk:
    if score >= config.excellent_threshold:
        return QualityRisk.EXCELLENT

    if score >= config.good_threshold:
        return QualityRisk.GOOD

    if score >= config.fair_threshold:
        return QualityRisk.FAIR

    if score >= config.poor_threshold:
        return QualityRisk.POOR

    return QualityRisk.CRITICAL


def calculate_quality_score(
    report: DatasetQualityReport,
    config: QualityScoringConfig | None = None,
) -> QualityScore:
    config = config or QualityScoringConfig()

    if not report.results:
        return QualityScore(
            dataset=report.dataset,
            score=100.0,
            risk=QualityRisk.EXCELLENT,
            rule_scores=(),
        )

    row_count = max(report.row_count, 1)
    rule_scores: list[QualityRuleScore] = []

    for result in report.results:
        if not result.issues:
            rule_scores.append(
                QualityRuleScore(
                    rule_name=result.rule_name,
                    score=100.0,
                    impact=0.0,
                    issue_count=0,
                    affected_rows=0,
                )
            )
            continue

        total_impact = 0.0
        affected_rows = 0

        for issue in result.issues:
            affected_rows += issue.affected_rows

            row_ratio = min(
                issue.affected_rows / row_count,
                1.0,
            )

            total_impact += (
                _severity_weight(issue.severity, config)
                * row_ratio
            )

        impact = min(total_impact, 1.0)
        score = max(0.0, 100.0 * (1.0 - impact))

        rule_scores.append(
            QualityRuleScore(
                rule_name=result.rule_name,
                score=round(score, 2),
                impact=round(impact, 4),
                issue_count=result.issue_count,
                affected_rows=affected_rows,
            )
        )

    overall_score = sum(
        rule_score.score
        for rule_score in rule_scores
    ) / len(rule_scores)

    overall_score = round(
        max(0.0, min(100.0, overall_score)),
        2,
    )

    return QualityScore(
        dataset=report.dataset,
        score=overall_score,
        risk=_risk_from_score(
            overall_score,
            config,
        ),
        rule_scores=tuple(rule_scores),
    )


def score_quality_report(
    report: DatasetQualityReport,
    config: QualityScoringConfig | None = None,
) -> dict:
    quality_score = calculate_quality_score(
        report,
        config,
    )

    return {
        "dataset": quality_score.dataset,
        "score": quality_score.score,
        "risk": quality_score.risk.value,
        "rule_count": quality_score.rule_count,
        "failed_rule_count": quality_score.failed_rule_count,
        "rules": [
            {
                "rule_name": rule.rule_name,
                "score": rule.score,
                "impact": rule.impact,
                "issue_count": rule.issue_count,
                "affected_rows": rule.affected_rows,
            }
            for rule in quality_score.rule_scores
        ],
    }
