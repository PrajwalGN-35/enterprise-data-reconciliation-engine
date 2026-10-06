import pandas as pd
import pytest

from backend.app.services.data_quality.anomaly import (
    AnomalyConfig,
    AnomalyRule,
)
from backend.app.services.data_quality.engine import (
    DataQualityEngine,
    QualitySeverity,
)
from backend.app.services.data_quality.scoring import (
    QualityRisk,
    QualityScoringConfig,
    calculate_quality_score,
    score_quality_report,
)


def test_clean_dataset_scores_excellent():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 104],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [AnomalyConfig("amount")]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    quality_score = calculate_quality_score(report)

    assert quality_score.score == 100.0
    assert quality_score.risk == QualityRisk.EXCELLENT
    assert quality_score.rule_count == 1
    assert quality_score.failed_rule_count == 0


def test_error_issue_reduces_score():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 1000],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [
                AnomalyConfig(
                    "amount",
                    severity=QualitySeverity.ERROR,
                )
            ]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    quality_score = calculate_quality_score(report)

    assert quality_score.score < 100.0
    assert quality_score.failed_rule_count == 1
    assert quality_score.rule_scores[0].issue_count == 1


def test_critical_issue_has_higher_impact():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 1000],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [
                AnomalyConfig(
                    "amount",
                    severity=QualitySeverity.CRITICAL,
                )
            ]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    quality_score = calculate_quality_score(report)

    assert quality_score.score < 100.0
    assert quality_score.rule_scores[0].impact > 0.0


def test_risk_classification():
    config = QualityScoringConfig(
        excellent_threshold=95.0,
        good_threshold=85.0,
        fair_threshold=70.0,
        poor_threshold=50.0,
    )

    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 1000],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [
                AnomalyConfig(
                    "amount",
                    severity=QualitySeverity.CRITICAL,
                )
            ]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    quality_score = calculate_quality_score(
        report,
        config,
    )

    assert quality_score.risk in {
        QualityRisk.GOOD,
        QualityRisk.FAIR,
        QualityRisk.POOR,
        QualityRisk.CRITICAL,
    }


def test_empty_report_scores_excellent():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 200],
        }
    )

    engine = DataQualityEngine()

    report = engine.run(
        dataframe,
        "transactions",
    )

    quality_score = calculate_quality_score(report)

    assert quality_score.score == 100.0
    assert quality_score.risk == QualityRisk.EXCELLENT


def test_multiple_anomaly_configs_are_aggregated():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 1000],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [
                AnomalyConfig(
                    "amount",
                    method="iqr",
                    severity=QualitySeverity.WARNING,
                ),
                AnomalyConfig(
                    "amount",
                    method="zscore",
                    threshold=1.0,
                    severity=QualitySeverity.ERROR,
                ),
            ]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    quality_score = calculate_quality_score(report)

    assert quality_score.rule_count == 1
    assert quality_score.failed_rule_count == 1
    assert quality_score.rule_scores[0].issue_count >= 1
    assert 0.0 <= quality_score.score <= 100.0


def test_custom_weights_change_score():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 1000],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [
                AnomalyConfig(
                    "amount",
                    severity=QualitySeverity.WARNING,
                )
            ]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    default_score = calculate_quality_score(report)

    strict_config = QualityScoringConfig(
        warning_weight=0.50,
    )

    strict_score = calculate_quality_score(
        report,
        strict_config,
    )

    assert strict_score.score < default_score.score


def test_score_quality_report_returns_dashboard_payload():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 1000],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [AnomalyConfig("amount")]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    payload = score_quality_report(report)

    assert payload["dataset"] == "transactions"
    assert 0.0 <= payload["score"] <= 100.0
    assert payload["risk"] in {
        "EXCELLENT",
        "GOOD",
        "FAIR",
        "POOR",
        "CRITICAL",
    }
    assert len(payload["rules"]) == 1


def test_invalid_weights_rejected():
    with pytest.raises(ValueError):
        QualityScoringConfig(
            warning_weight=-0.1,
        )


def test_invalid_thresholds_rejected():
    with pytest.raises(ValueError):
        QualityScoringConfig(
            excellent_threshold=80.0,
            good_threshold=90.0,
        )


def test_score_is_bounded():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 102, 103, 1000],
        }
    )

    engine = DataQualityEngine()

    engine.register(
        AnomalyRule(
            [
                AnomalyConfig(
                    "amount",
                    severity=QualitySeverity.CRITICAL,
                )
            ]
        )
    )

    report = engine.run(
        dataframe,
        "transactions",
    )

    quality_score = calculate_quality_score(report)

    assert 0.0 <= quality_score.score <= 100.0
