from dataclasses import dataclass
import re
from collections.abc import Callable
import pandas as pd
from .engine import QualityIssue, QualityRuleResult, QualitySeverity


@dataclass(frozen=True)
class ValidityConfig:
    column: str
    validator: str
    severity: QualitySeverity = QualitySeverity.ERROR
    allow_null: bool = True
    pattern: str | None = None
    min_value: float | None = None
    max_value: float | None = None

    def __post_init__(self) -> None:
        if not self.column:
            raise ValueError("column must not be empty")
        allowed = {"email", "regex", "numeric_range", "date"}
        if self.validator not in allowed:
            raise ValueError(
                f"validator must be one of: {', '.join(sorted(allowed))}"
            )
        if self.validator == "regex" and not self.pattern:
            raise ValueError("pattern is required for regex validation")
        if self.validator == "numeric_range":
            if self.min_value is None and self.max_value is None:
                raise ValueError(
                    "min_value or max_value is required for numeric_range validation"
                )
            if (
                self.min_value is not None
                and self.max_value is not None
                and self.min_value > self.max_value
            ):
                raise ValueError("min_value cannot exceed max_value")


class ValidityRule:
    name = "validity"

    def __init__(self, config: ValidityConfig) -> None:
        self.config = config

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        dataset: str,
    ) -> QualityRuleResult:
        column = self.config.column

        if column not in dataframe.columns:
            issue = QualityIssue(
                rule_name=self.name,
                dataset=dataset,
                severity=QualitySeverity.CRITICAL,
                message=f"Validity column '{column}' is missing from the dataset.",
                affected_rows=len(dataframe),
                column=column,
                metadata={
                    "issue_type": "missing_column",
                    "validator": self.config.validator,
                },
            )
            return QualityRuleResult(
                rule_name=self.name,
                passed=False,
                issues=(issue,),
            )

        series = dataframe[column]

        if self.config.allow_null:
            candidate = series.dropna()
        else:
            candidate = series

        invalid_mask = pd.Series(False, index=series.index)

        if self.config.validator == "email":
            invalid_mask = ~candidate.astype(str).str.match(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                na=False,
            )

        elif self.config.validator == "regex":
            invalid_mask = ~candidate.astype(str).str.match(
                self.config.pattern or "",
                na=False,
            )

        elif self.config.validator == "numeric_range":
            numeric = pd.to_numeric(candidate, errors="coerce")
            invalid_mask = numeric.isna()
            if self.config.min_value is not None:
                invalid_mask = invalid_mask | (
                    numeric < self.config.min_value
                )
            if self.config.max_value is not None:
                invalid_mask = invalid_mask | (
                    numeric > self.config.max_value
                )

        elif self.config.validator == "date":
            parsed = pd.to_datetime(candidate, errors="coerce")
            invalid_mask = parsed.isna()

        invalid_rows = int(invalid_mask.sum())

        if invalid_rows == 0:
            return QualityRuleResult(
                rule_name=self.name,
                passed=True,
                issues=(),
            )

        issue = QualityIssue(
            rule_name=self.name,
            dataset=dataset,
            severity=self.config.severity,
            message=(
                f"Found {invalid_rows} invalid value(s) in column "
                f"'{column}' using {self.config.validator} validation."
            ),
            affected_rows=invalid_rows,
            column=column,
            metadata={
                "issue_type": "invalid_value",
                "validator": self.config.validator,
                "invalid_rows": invalid_rows,
                "allow_null": self.config.allow_null,
                "pattern": self.config.pattern,
                "min_value": self.config.min_value,
                "max_value": self.config.max_value,
            },
        )

        return QualityRuleResult(
            rule_name=self.name,
            passed=False,
            issues=(issue,),
        )


def validate_column(
    dataframe: pd.DataFrame,
    config: ValidityConfig,
) -> pd.Series:
    if config.column not in dataframe.columns:
        raise ValueError(
            f"Missing validity column: {config.column}"
        )

    series = dataframe[config.column]

    if config.allow_null:
        candidate = series.dropna()
    else:
        candidate = series

    if config.validator == "email":
        return candidate.astype(str).str.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            na=False,
        )

    if config.validator == "regex":
        return candidate.astype(str).str.match(
            config.pattern or "",
            na=False,
        )

    if config.validator == "numeric_range":
        numeric = pd.to_numeric(candidate, errors="coerce")
        valid = numeric.notna()
        if config.min_value is not None:
            valid = valid & (numeric >= config.min_value)
        if config.max_value is not None:
            valid = valid & (numeric <= config.max_value)
        return valid

    if config.validator == "date":
        return pd.to_datetime(candidate, errors="coerce").notna()

    raise ValueError(f"Unsupported validator: {config.validator}")