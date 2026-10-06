import pandas as pd
import pytest

from backend.app.services.data_quality.duplicates import (
    DuplicateConfig,
    DuplicateRule,
    find_duplicate_groups,
)
from backend.app.services.data_quality.engine import (
    DataQualityEngine,
    QualitySeverity,
)


def test_duplicate_rule_passes_for_unique_keys() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "email": ["a@example.com", "b@example.com", "c@example.com"],
        }
    )

    rule = DuplicateRule(
        DuplicateConfig(key_columns=("customer_id",))
    )

    result = rule.evaluate(dataframe, "customers")

    assert result.passed
    assert result.issues == ()


def test_duplicate_rule_detects_duplicate_business_keys() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C001", "C003", "C003"],
            "email": [
                "a@example.com",
                "b@example.com",
                "other@example.com",
                "c@example.com",
                "third@example.com",
            ],
        }
    )

    rule = DuplicateRule(
        DuplicateConfig(key_columns=("customer_id",))
    )

    result = rule.evaluate(dataframe, "customers")

    assert not result.passed
    assert len(result.issues) == 1
    assert result.issues[0].affected_rows == 4
    assert result.issues[0].severity == QualitySeverity.ERROR
    assert result.issues[0].metadata["duplicate_groups"] == 2
    assert result.issues[0].metadata["duplicate_rows"] == 4
    assert result.issues[0].metadata["key_columns"] == ["customer_id"]


def test_composite_business_key_is_supported() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C001", "C001"],
            "region_id": ["R01", "R01", "R02"],
        }
    )

    rule = DuplicateRule(
        DuplicateConfig(key_columns=("customer_id", "region_id"))
    )

    result = rule.evaluate(dataframe, "customers")

    assert not result.passed
    assert result.issues[0].affected_rows == 2
    assert result.issues[0].metadata["duplicate_groups"] == 1


def test_null_keys_are_excluded_by_default() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", None, None],
        }
    )

    rule = DuplicateRule(
        DuplicateConfig(key_columns=("customer_id",))
    )

    result = rule.evaluate(dataframe, "customers")

    assert result.passed


def test_null_keys_can_be_included() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", None, None],
        }
    )

    rule = DuplicateRule(
        DuplicateConfig(
            key_columns=("customer_id",),
            include_null_keys=True,
        )
    )

    result = rule.evaluate(dataframe, "customers")

    assert not result.passed
    assert result.issues[0].affected_rows == 2


def test_missing_key_column_is_critical() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C002"],
        }
    )

    rule = DuplicateRule(
        DuplicateConfig(key_columns=("email",))
    )

    result = rule.evaluate(dataframe, "customers")

    assert not result.passed
    assert len(result.issues) == 1
    assert result.issues[0].severity == QualitySeverity.CRITICAL
    assert result.issues[0].metadata["issue_type"] == "missing_key_column"


def test_find_duplicate_groups_returns_only_duplicate_rows() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C001", "C003"],
            "email": ["a", "b", "a2", "c"],
        }
    )

    duplicates = find_duplicate_groups(
        dataframe,
        ("customer_id",),
    )

    assert len(duplicates) == 2
    assert set(duplicates["customer_id"]) == {"C001"}


def test_duplicate_rule_integrates_with_engine() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C001"],
        }
    )

    engine = DataQualityEngine()
    engine.register(
        DuplicateRule(
            DuplicateConfig(key_columns=("customer_id",))
        )
    )

    report = engine.run(dataframe, "customers")

    assert report.dataset == "customers"
    assert report.row_count == 3
    assert report.column_count == 1
    assert report.issue_count == 1
    assert report.failed_rules == 1


def test_duplicate_config_requires_key_columns() -> None:
    with pytest.raises(ValueError, match="key_columns"):
        DuplicateConfig()