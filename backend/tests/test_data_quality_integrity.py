import pandas as pd
import pytest

from backend.app.services.data_quality.engine import (
    QualitySeverity,
)
from backend.app.services.data_quality.integrity import (
    ConditionalRequirementConfig,
    ConditionalRequirementRule,
    CrossFieldConfig,
    CrossFieldRule,
    ReferentialIntegrityConfig,
    ReferentialIntegrityRule,
    validate_cross_field,
)


def test_cross_field_less_than_or_equal():
    dataframe = pd.DataFrame(
        {
            "start": [1, 2, 5],
            "end": [2, 2, 3],
        }
    )

    result = CrossFieldRule(
        [CrossFieldConfig("start", "le", "end")]
    ).evaluate(dataframe, "orders")

    assert not result.passed
    assert result.issue_count == 1
    assert result.issues[0].affected_rows == 1
    assert result.issues[0].metadata["issue_type"] == "cross_field_violation"


def test_cross_field_valid_data_passes():
    dataframe = pd.DataFrame(
        {
            "start": [1, 2, 3],
            "end": [2, 2, 4],
        }
    )

    result = CrossFieldRule(
        [CrossFieldConfig("start", "le", "end")]
    ).evaluate(dataframe, "orders")

    assert result.passed
    assert result.issues == ()


def test_cross_field_missing_column_is_critical():
    dataframe = pd.DataFrame({"start": [1, 2]})

    result = CrossFieldRule(
        [CrossFieldConfig("start", "le", "end")]
    ).evaluate(dataframe, "orders")

    assert not result.passed
    assert result.issues[0].severity == QualitySeverity.CRITICAL
    assert result.issues[0].metadata["issue_type"] == "missing_column"


def test_cross_field_nulls_allowed():
    dataframe = pd.DataFrame(
        {
            "start": [1, None],
            "end": [2, None],
        }
    )

    result = CrossFieldRule(
        [CrossFieldConfig("start", "le", "end", allow_null=True)]
    ).evaluate(dataframe, "orders")

    assert result.passed


def test_cross_field_nulls_rejected():
    dataframe = pd.DataFrame(
        {
            "start": [1, None],
            "end": [2, None],
        }
    )

    result = CrossFieldRule(
        [CrossFieldConfig("start", "le", "end", allow_null=False)]
    ).evaluate(dataframe, "orders")

    assert not result.passed
    assert result.issues[0].affected_rows == 1


def test_conditional_requirement():
    dataframe = pd.DataFrame(
        {
            "status": ["active", "active", "inactive"],
            "email": ["a@test.com", "", ""],
        }
    )

    result = ConditionalRequirementRule(
        [ConditionalRequirementConfig("status", "active", "email")]
    ).evaluate(dataframe, "customers")

    assert not result.passed
    assert result.issues[0].affected_rows == 1
    assert (
        result.issues[0].metadata["issue_type"]
        == "conditional_requirement_violation"
    )


def test_conditional_requirement_passes():
    dataframe = pd.DataFrame(
        {
            "status": ["active", "inactive"],
            "email": ["a@test.com", ""],
        }
    )

    result = ConditionalRequirementRule(
        [ConditionalRequirementConfig("status", "active", "email")]
    ).evaluate(dataframe, "customers")

    assert result.passed


def test_conditional_requirement_missing_columns():
    dataframe = pd.DataFrame({"status": ["active"]})

    result = ConditionalRequirementRule(
        [ConditionalRequirementConfig("status", "active", "email")]
    ).evaluate(dataframe, "customers")

    assert result.issues[0].severity == QualitySeverity.CRITICAL


def test_referential_integrity_detects_orphans():
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 99],
            "known_customer_id": [1, 2, 3],
        }
    )

    result = ReferentialIntegrityRule(
        [ReferentialIntegrityConfig("customer_id", "known_customer_id")]
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issues[0].affected_rows == 1
    assert result.issues[0].metadata["issue_type"] == "orphan_reference"


def test_referential_integrity_passes():
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "known_customer_id": [1, 2],
        }
    )

    result = ReferentialIntegrityRule(
        [ReferentialIntegrityConfig("customer_id", "known_customer_id")]
    ).evaluate(dataframe, "transactions")

    assert result.passed


def test_referential_integrity_allows_null():
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, None],
            "known_customer_id": [1, 2],
        }
    )

    result = ReferentialIntegrityRule(
        [ReferentialIntegrityConfig("customer_id", "known_customer_id")]
    ).evaluate(dataframe, "transactions")

    assert result.passed


def test_referential_integrity_missing_column():
    dataframe = pd.DataFrame({"customer_id": [1, 2]})

    result = ReferentialIntegrityRule(
        [ReferentialIntegrityConfig("customer_id", "known_customer_id")]
    ).evaluate(dataframe, "transactions")

    assert result.issues[0].severity == QualitySeverity.CRITICAL


def test_cross_field_helper():
    dataframe = pd.DataFrame(
        {
            "min": [1, 5, 8],
            "max": [2, 4, 9],
        }
    )

    result = validate_cross_field(
        dataframe,
        "min",
        "le",
        "max",
    )

    assert result.tolist() == [True, False, True]


def test_invalid_operator_rejected():
    with pytest.raises(ValueError):
        CrossFieldConfig("a", "between", "b")


def test_engine_integration():
    from backend.app.services.data_quality.engine import DataQualityEngine

    dataframe = pd.DataFrame(
        {
            "start": [1, 5],
            "end": [2, 3],
        }
    )

    engine = DataQualityEngine()
    engine.register(
        CrossFieldRule(
            [CrossFieldConfig("start", "le", "end")]
        )
    )

    report = engine.run(dataframe, "orders")

    assert report.dataset == "orders"
    assert report.row_count == 2
    assert report.failed_rules == 1
    assert report.issue_count == 1
