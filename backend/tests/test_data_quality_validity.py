import pandas as pd
import pytest

from backend.app.services.data_quality.validity import (
    ValidityConfig,
    ValidityRule,
    validate_column,
)
from backend.app.services.data_quality.engine import (
    DataQualityEngine,
    QualitySeverity,
)


def test_email_validation_passes_for_valid_values() -> None:
    dataframe = pd.DataFrame(
        {"email": ["a@example.com", "user@test.org"]}
    )

    result = ValidityRule(
        ValidityConfig(column="email", validator="email")
    ).evaluate(dataframe, "customers")

    assert result.passed
    assert result.issues == ()


def test_email_validation_detects_invalid_values() -> None:
    dataframe = pd.DataFrame(
        {"email": ["a@example.com", "invalid", "x@", "bad@test.org"]}
    )

    result = ValidityRule(
        ValidityConfig(column="email", validator="email")
    ).evaluate(dataframe, "customers")

    assert not result.passed
    assert result.issues[0].affected_rows == 2
    assert result.issues[0].severity == QualitySeverity.ERROR


def test_regex_validation() -> None:
    dataframe = pd.DataFrame(
        {"customer_id": ["C001", "C002", "BAD", "C004"]}
    )

    result = ValidityRule(
        ValidityConfig(
            column="customer_id",
            validator="regex",
            pattern=r"^C\d{3}$",
        )
    ).evaluate(dataframe, "customers")

    assert not result.passed
    assert result.issues[0].affected_rows == 1


def test_numeric_range_validation() -> None:
    dataframe = pd.DataFrame(
        {"amount": [100, 500, 1000, 1500]}
    )

    result = ValidityRule(
        ValidityConfig(
            column="amount",
            validator="numeric_range",
            min_value=100,
            max_value=1000,
        )
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issues[0].affected_rows == 1


def test_numeric_range_rejects_non_numeric_values() -> None:
    dataframe = pd.DataFrame(
        {"amount": [100, "bad", 500]}
    )

    result = ValidityRule(
        ValidityConfig(
            column="amount",
            validator="numeric_range",
            min_value=0,
            max_value=1000,
        )
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issues[0].affected_rows == 1


def test_date_validation() -> None:
    dataframe = pd.DataFrame(
        {"transaction_date": ["2026-01-01", "2026-02-15", "not-a-date"]}
    )

    result = ValidityRule(
        ValidityConfig(
            column="transaction_date",
            validator="date",
        )
    ).evaluate(dataframe, "transactions")

    assert not result.passed
    assert result.issues[0].affected_rows == 1


def test_null_values_are_allowed_by_default() -> None:
    dataframe = pd.DataFrame(
        {"email": ["a@example.com", None, "b@example.com"]}
    )

    result = ValidityRule(
        ValidityConfig(column="email", validator="email")
    ).evaluate(dataframe, "customers")

    assert result.passed


def test_null_values_can_be_invalid() -> None:
    dataframe = pd.DataFrame(
        {"email": ["a@example.com", None]}
    )

    result = ValidityRule(
        ValidityConfig(
            column="email",
            validator="email",
            allow_null=False,
        )
    ).evaluate(dataframe, "customers")

    assert not result.passed
    assert result.issues[0].affected_rows == 1


def test_missing_column_is_critical() -> None:
    dataframe = pd.DataFrame({"customer_id": ["C001"]})

    result = ValidityRule(
        ValidityConfig(column="email", validator="email")
    ).evaluate(dataframe, "customers")

    assert not result.passed
    assert result.issues[0].severity == QualitySeverity.CRITICAL
    assert result.issues[0].metadata["issue_type"] == "missing_column"


def test_engine_integration() -> None:
    dataframe = pd.DataFrame(
        {"email": ["good@example.com", "bad"]}
    )

    engine = DataQualityEngine()
    engine.register(
        ValidityRule(
            ValidityConfig(column="email", validator="email")
        )
    )

    report = engine.run(dataframe, "customers")

    assert report.dataset == "customers"
    assert report.row_count == 2
    assert report.column_count == 1
    assert report.issue_count == 1
    assert report.failed_rules == 1


def test_validate_column_returns_boolean_series() -> None:
    dataframe = pd.DataFrame(
        {"customer_id": ["C001", "BAD", "C003"]}
    )

    result = validate_column(
        dataframe,
        ValidityConfig(
            column="customer_id",
            validator="regex",
            pattern=r"^C\d{3}$",
        ),
    )

    assert result.tolist() == [True, False, True]


def test_invalid_validator_is_rejected() -> None:
    with pytest.raises(ValueError, match="validator"):
        ValidityConfig(
            column="email",
            validator="unknown",
        )


def test_regex_requires_pattern() -> None:
    with pytest.raises(ValueError, match="pattern"):
        ValidityConfig(
            column="customer_id",
            validator="regex",
        )


def test_numeric_range_requires_bounds() -> None:
    with pytest.raises(ValueError, match="min_value or max_value"):
        ValidityConfig(
            column="amount",
            validator="numeric_range",
        )