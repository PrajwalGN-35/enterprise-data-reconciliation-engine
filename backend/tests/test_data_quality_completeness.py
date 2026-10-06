import pandas as pd
import pytest

from backend.app.services.data_quality.completeness import (
    CompletenessConfig,
    CompletenessRule,
    calculate_completeness,
)
from backend.app.services.data_quality.engine import (
    DataQualityEngine,
    QualitySeverity,
)


def test_clean_dataset_passes_completeness_rule() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C002"],
            "email": ["a@example.com", "b@example.com"],
        }
    )

    rule = CompletenessRule(
        CompletenessConfig(required_columns=("customer_id", "email"))
    )

    result = rule.evaluate(dataframe, "customers")

    assert result.passed
    assert result.issues == ()


def test_required_column_missing_is_critical() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C002"],
        }
    )

    rule = CompletenessRule(
        CompletenessConfig(required_columns=("customer_id", "email"))
    )

    result = rule.evaluate(dataframe, "customers")
    issues = result.issues

    assert not result.passed
    assert len(issues) == 1
    assert issues[0].column == "email"
    assert issues[0].severity == QualitySeverity.CRITICAL
    assert issues[0].metadata["issue_type"] == "missing_required_column"


def test_null_rate_is_detected() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", None, "C003", "C004"],
        }
    )

    rule = CompletenessRule(
        CompletenessConfig(
            required_columns=("customer_id",),
            max_null_rate=0.10,
        )
    )

    result = rule.evaluate(dataframe, "customers")
    issues = result.issues

    assert not result.passed
    assert len(issues) == 1
    assert issues[0].affected_rows == 1
    assert issues[0].column == "customer_id"
    assert issues[0].metadata["null_rate"] == pytest.approx(0.25)
    assert issues[0].metadata["completeness"] == pytest.approx(0.75)


def test_blank_strings_are_treated_as_missing() -> None:
    dataframe = pd.DataFrame(
        {
            "email": ["a@example.com", "   ", "b@example.com"],
        }
    )

    rule = CompletenessRule(
        CompletenessConfig(
            required_columns=("email",),
            max_null_rate=0.0,
        )
    )

    result = rule.evaluate(dataframe, "customers")
    issues = result.issues

    assert not result.passed
    assert len(issues) == 1
    assert issues[0].affected_rows == 1


def test_null_rate_threshold_can_allow_missing_values() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", None, "C003", "C004"],
        }
    )

    rule = CompletenessRule(
        CompletenessConfig(
            required_columns=("customer_id",),
            max_null_rate=0.25,
        )
    )

    result = rule.evaluate(dataframe, "customers")

    assert result.passed
    assert result.issues == ()


def test_completeness_calculation() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", None, "C003", "C004"],
            "email": ["a@example.com", "b@example.com", " ", None],
        }
    )

    result = calculate_completeness(dataframe)

    assert result["customer_id"] == pytest.approx(0.75)
    assert result["email"] == pytest.approx(0.50)


def test_completeness_rule_integrates_with_engine() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", None],
            "email": ["a@example.com", "b@example.com"],
        }
    )

    engine = DataQualityEngine()
    engine.register(
        CompletenessRule(
            CompletenessConfig(
                required_columns=("customer_id", "email"),
                max_null_rate=0.0,
            )
        )
    )

    report = engine.run(dataframe, "customers")

    assert report.dataset == "customers"
    assert report.row_count == 2
    assert report.column_count == 2
    assert report.issue_count == 1
    assert report.failed_rules == 1