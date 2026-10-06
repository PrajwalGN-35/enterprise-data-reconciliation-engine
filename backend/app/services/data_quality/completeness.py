from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .engine import QualityIssue, QualityRule, QualityRuleResult, QualitySeverity


@dataclass(frozen=True)
class CompletenessConfig:
    required_columns: tuple[str, ...] = ()
    max_null_rate: float = 0.0
    blank_strings_are_missing: bool = True
    severity: QualitySeverity = QualitySeverity.ERROR

    def __post_init__(self) -> None:
        if not 0.0 <= self.max_null_rate <= 1.0:
            raise ValueError("max_null_rate must be between 0.0 and 1.0")


class CompletenessRule:
    name = "completeness"

    def __init__(
        self,
        config: CompletenessConfig | None = None,
    ) -> None:
        self.config = config or CompletenessConfig()

    def _missing_mask(self, series: pd.Series) -> pd.Series:
        missing = series.isna()
        if self.config.blank_strings_are_missing:
            missing = missing | (
                series.astype("string").str.strip().eq("").fillna(False)
            )
        return missing

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        dataset: str,
    ) -> QualityRuleResult:
        issues: list[QualityIssue] = []

        required_columns = set(self.config.required_columns)
        missing_columns = [
            column
            for column in self.config.required_columns
            if column not in dataframe.columns
        ]

        for column in missing_columns:
            issues.append(
                QualityIssue(
                    rule_name=self.name,
                    dataset=dataset,
                    severity=QualitySeverity.CRITICAL,
                    message=f"Required column '{column}' is missing from the dataset.",
                    affected_rows=len(dataframe),
                    column=column,
                    metadata={"issue_type": "missing_required_column"},
                )
            )

        columns_to_check: Iterable[str]
        if required_columns:
            columns_to_check = [
                column
                for column in dataframe.columns
                if column in required_columns
            ]
        else:
            columns_to_check = dataframe.columns

        for column in columns_to_check:
            missing_mask = self._missing_mask(dataframe[column])
            affected_rows = int(missing_mask.sum())
            null_rate = (
                affected_rows / len(dataframe)
                if len(dataframe) > 0
                else 0.0
            )
            completeness = 1.0 - null_rate

            if null_rate > self.config.max_null_rate:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=self.config.severity,
                        message=(
                            f"Column '{column}' has {affected_rows} missing "
                            f"values ({null_rate:.2%}); maximum allowed is "
                            f"{self.config.max_null_rate:.2%}."
                        ),
                        affected_rows=affected_rows,
                        column=column,
                        metadata={
                            "issue_type": "null_rate_exceeded",
                            "null_rate": null_rate,
                            "completeness": completeness,
                            "max_null_rate": self.config.max_null_rate,
                        },
                    )
                )

        return QualityRuleResult(rule_name=self.name, passed=not issues, issues=tuple(issues))


def calculate_completeness(
    dataframe: pd.DataFrame,
    columns: Iterable[str] | None = None,
    blank_strings_are_missing: bool = True,
) -> dict[str, float]:
    selected_columns = (
        list(columns) if columns is not None else list(dataframe.columns)
    )

    result: dict[str, float] = {}

    for column in selected_columns:
        if column not in dataframe.columns:
            continue

        missing = dataframe[column].isna()

        if blank_strings_are_missing:
            missing = missing | (
                dataframe[column]
                .astype("string")
                .str.strip()
                .eq("")
                .fillna(False)
            )

        null_rate = (
            int(missing.sum()) / len(dataframe)
            if len(dataframe) > 0
            else 0.0
        )

        result[column] = 1.0 - null_rate

    return result