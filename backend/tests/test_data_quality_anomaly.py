import pandas as pd
import pytest

from backend.app.services.data_quality.engine import QualitySeverity
from backend.app.services.data_quality.anomaly import (
    AnomalyConfig,
    AnomalyRule,
    detect_iqr_outliers,
    detect_zscore_anomalies,
)


def test_iqr_detects_outlier():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 102, 98, 101, 99, 103, 1000],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig("amount", method="iqr")]
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issue_count == 1
    assert result.issues[0].affected_rows == 1
    assert result.issues[0].metadata["method"] == "iqr"
    assert result.issues[0].metadata["issue_type"] == "statistical_anomaly"


def test_iqr_normal_data_passes():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 102, 98, 101, 99, 103, 104],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig("amount", method="iqr")]
    ).evaluate(dataframe, "transactions")

    assert result.passed


def test_zscore_detects_anomaly():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 99, 102, 98, 100, 500],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig(
            "amount",
            method="zscore",
            threshold=2.0,
        )]
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issues[0].affected_rows == 1
    assert result.issues[0].metadata["method"] == "zscore"


def test_zscore_normal_data_passes():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 99, 102, 98, 100, 101],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig(
            "amount",
            method="zscore",
            threshold=3.0,
        )]
    ).evaluate(dataframe, "transactions")

    assert result.passed


def test_missing_column_is_critical():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 200, 300],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig("revenue")]
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issues[0].severity == QualitySeverity.CRITICAL
    assert result.issues[0].metadata["issue_type"] == "missing_column"


def test_minimum_sample_protection():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 1000],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig(
            "amount",
            min_samples=5,
        )]
    ).evaluate(dataframe, "transactions")

    assert result.passed


def test_nulls_are_allowed_by_default():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 102, 98, 101, 99, None, 103],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig("amount")]
    ).evaluate(dataframe, "transactions")

    assert result.passed


def test_nulls_can_be_rejected():
    dataframe = pd.DataFrame(
        {
            "amount": [100, 102, 98, 101, 99, None, 103],
        }
    )

    result = AnomalyRule(
        [AnomalyConfig(
            "amount",
            allow_null=False,
        )]
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issues[0].metadata["issue_type"] == "invalid_numeric_value"


def test_iqr_helper():
    series = pd.Series([10, 11, 12, 10, 11, 100])

    result = detect_iqr_outliers(series)

    assert result.tolist() == [
        False,
        False,
        False,
        False,
        False,
        True,
    ]


def test_zscore_helper():
    series = pd.Series([10, 10, 10, 10, 10, 100])

    result = detect_zscore_anomalies(
        series,
        threshold=1.5,
    )

    assert result.iloc[-1]


def test_invalid_method_rejected():
    with pytest.raises(ValueError):
        AnomalyConfig(
            "amount",
            method="isolation_forest",
        )


def test_invalid_threshold_rejected():
    with pytest.raises(ValueError):
        AnomalyConfig(
            "amount",
            threshold=0,
        )


def test_engine_integration():
    from backend.app.services.data_quality.engine import DataQualityEngine

    dataframe = pd.DataFrame(
        {
            "amount": [100, 101, 99, 100, 102, 1000],
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

    assert report.dataset == "transactions"
    assert report.row_count == 6
    assert report.failed_rules == 1
    assert report.issue_count == 1
