from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd

from .engine import QualityIssue, QualityRuleResult, QualitySeverity


@dataclass(frozen=True)
class CrossFieldConfig:
    left_column: str
    operator: str
    right_column: str
    severity: QualitySeverity = QualitySeverity.ERROR
    allow_null: bool = True

    def __post_init__(self) -> None:
        allowed = {"eq", "ne", "lt", "le", "gt", "ge"}

        if not self.left_column:
            raise ValueError("left_column must not be empty")

        if not self.right_column:
            raise ValueError("right_column must not be empty")

        if self.operator not in allowed:
            raise ValueError(
                f"operator must be one of: {', '.join(sorted(allowed))}"
            )


@dataclass(frozen=True)
class ConditionalRequirementConfig:
    condition_column: str
    condition_value: Any
    required_column: str
    severity: QualitySeverity = QualitySeverity.ERROR

    def __post_init__(self) -> None:
        if not self.condition_column:
            raise ValueError("condition_column must not be empty")

        if not self.required_column:
            raise ValueError("required_column must not be empty")


@dataclass(frozen=True)
class ReferentialIntegrityConfig:
    child_column: str
    parent_column: str
    severity: QualitySeverity = QualitySeverity.ERROR
    allow_null: bool = True

    def __post_init__(self) -> None:
        if not self.child_column:
            raise ValueError("child_column must not be empty")

        if not self.parent_column:
            raise ValueError("parent_column must not be empty")


class CrossFieldRule:
    name = "cross_field_integrity"

    def __init__(
        self,
        configs: Iterable[CrossFieldConfig],
    ) -> None:
        self.configs = tuple(configs)

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        dataset: str,
    ) -> QualityRuleResult:
        issues: list[QualityIssue] = []

        for config in self.configs:
            missing_columns = [
                column
                for column in (
                    config.left_column,
                    config.right_column,
                )
                if column not in dataframe.columns
            ]

            if missing_columns:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=QualitySeverity.CRITICAL,
                        message=(
                            "Required cross-field column(s) are missing: "
                            f"{', '.join(missing_columns)}."
                        ),
                        affected_rows=len(dataframe),
                        column=", ".join(missing_columns),
                        metadata={
                            "issue_type": "missing_column",
                            "columns": missing_columns,
                        },
                    )
                )
                continue

            left = dataframe[config.left_column]
            right = dataframe[config.right_column]

            if config.operator == "eq":
                valid = left.eq(right)
            elif config.operator == "ne":
                valid = left.ne(right)
            elif config.operator == "lt":
                valid = left.lt(right)
            elif config.operator == "le":
                valid = left.le(right)
            elif config.operator == "gt":
                valid = left.gt(right)
            else:
                valid = left.ge(right)

            if config.allow_null:
                valid = valid | left.isna() | right.isna()

            invalid_count = int((~valid.fillna(False)).sum())

            if invalid_count:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=config.severity,
                        message=(
                            f"Cross-field rule failed: "
                            f"'{config.left_column}' "
                            f"{config.operator} "
                            f"'{config.right_column}'."
                        ),
                        affected_rows=invalid_count,
                        column=(
                            f"{config.left_column}, "
                            f"{config.right_column}"
                        ),
                        metadata={
                            "issue_type": "cross_field_violation",
                            "left_column": config.left_column,
                            "operator": config.operator,
                            "right_column": config.right_column,
                            "allow_null": config.allow_null,
                            "invalid_rows": invalid_count,
                        },
                    )
                )

        return QualityRuleResult(
            rule_name=self.name,
            passed=not issues,
            issues=tuple(issues),
        )


class ConditionalRequirementRule:
    name = "conditional_requirement"

    def __init__(
        self,
        configs: Iterable[ConditionalRequirementConfig],
    ) -> None:
        self.configs = tuple(configs)

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        dataset: str,
    ) -> QualityRuleResult:
        issues: list[QualityIssue] = []

        for config in self.configs:
            missing_columns = [
                column
                for column in (
                    config.condition_column,
                    config.required_column,
                )
                if column not in dataframe.columns
            ]

            if missing_columns:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=QualitySeverity.CRITICAL,
                        message=(
                            "Required conditional column(s) are missing: "
                            f"{', '.join(missing_columns)}."
                        ),
                        affected_rows=len(dataframe),
                        column=", ".join(missing_columns),
                        metadata={
                            "issue_type": "missing_column",
                            "columns": missing_columns,
                        },
                    )
                )
                continue

            condition = dataframe[config.condition_column].eq(
                config.condition_value
            )

            required = dataframe[config.required_column]

            empty = (
                required.isna()
                | required.astype("string").str.strip().eq("").fillna(False)
            )

            invalid_count = int((condition & empty).sum())

            if invalid_count:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=config.severity,
                        message=(
                            f"'{config.required_column}' is required when "
                            f"'{config.condition_column}' equals "
                            f"{config.condition_value!r}."
                        ),
                        affected_rows=invalid_count,
                        column=config.required_column,
                        metadata={
                            "issue_type": (
                                "conditional_requirement_violation"
                            ),
                            "condition_column": config.condition_column,
                            "condition_value": config.condition_value,
                            "required_column": config.required_column,
                            "invalid_rows": invalid_count,
                        },
                    )
                )

        return QualityRuleResult(
            rule_name=self.name,
            passed=not issues,
            issues=tuple(issues),
        )


class ReferentialIntegrityRule:
    name = "referential_integrity"

    def __init__(
        self,
        configs: Iterable[ReferentialIntegrityConfig],
    ) -> None:
        self.configs = tuple(configs)

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        dataset: str,
    ) -> QualityRuleResult:
        issues: list[QualityIssue] = []

        for config in self.configs:
            missing_columns = [
                column
                for column in (
                    config.child_column,
                    config.parent_column,
                )
                if column not in dataframe.columns
            ]

            if missing_columns:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=QualitySeverity.CRITICAL,
                        message=(
                            "Required referential column(s) are missing: "
                            f"{', '.join(missing_columns)}."
                        ),
                        affected_rows=len(dataframe),
                        column=", ".join(missing_columns),
                        metadata={
                            "issue_type": "missing_column",
                            "columns": missing_columns,
                        },
                    )
                )
                continue

            parent_values = set(
                dataframe[config.parent_column].dropna().tolist()
            )

            child = dataframe[config.child_column]

            valid = child.isin(parent_values)

            if config.allow_null:
                valid = valid | child.isna()

            invalid_count = int((~valid.fillna(False)).sum())

            if invalid_count:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=config.severity,
                        message=(
                            f"'{config.child_column}' contains "
                            "orphan references not present in "
                            f"'{config.parent_column}'."
                        ),
                        affected_rows=invalid_count,
                        column=config.child_column,
                        metadata={
                            "issue_type": "orphan_reference",
                            "child_column": config.child_column,
                            "parent_column": config.parent_column,
                            "allow_null": config.allow_null,
                            "reference_value_count": len(parent_values),
                            "invalid_rows": invalid_count,
                        },
                    )
                )

        return QualityRuleResult(
            rule_name=self.name,
            passed=not issues,
            issues=tuple(issues),
        )


def validate_cross_field(
    dataframe: pd.DataFrame,
    left_column: str,
    operator: str,
    right_column: str,
    allow_null: bool = True,
) -> pd.Series:
    config = CrossFieldConfig(
        left_column=left_column,
        operator=operator,
        right_column=right_column,
        allow_null=allow_null,
    )

    rule = CrossFieldRule([config])
    result = rule.evaluate(dataframe, "validation")

    invalid_count = (
        result.issues[0].affected_rows
        if result.issues
        else 0
    )

    left = dataframe[left_column]
    right = dataframe[right_column]

    if operator == "eq":
        valid = left.eq(right)
    elif operator == "ne":
        valid = left.ne(right)
    elif operator == "lt":
        valid = left.lt(right)
    elif operator == "le":
        valid = left.le(right)
    elif operator == "gt":
        valid = left.gt(right)
    else:
        valid = left.ge(right)

    if allow_null:
        valid = valid | left.isna() | right.isna()

    if invalid_count == 0:
        return valid.fillna(False)

    return valid.fillna(False)
