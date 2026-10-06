from dataclasses import dataclass

import pandas as pd

from .engine import QualityIssue, QualityRuleResult, QualitySeverity


@dataclass(frozen=True)
class DuplicateConfig:
    key_columns: tuple[str, ...] = ()
    include_null_keys: bool = False
    severity: QualitySeverity = QualitySeverity.ERROR

    def __post_init__(self) -> None:
        if not self.key_columns:
            raise ValueError("key_columns must contain at least one column")


class DuplicateRule:
    name = "uniqueness"

    def __init__(self, config: DuplicateConfig) -> None:
        self.config = config

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        dataset: str,
    ) -> QualityRuleResult:
        issues: list[QualityIssue] = []

        missing_columns = [
            column
            for column in self.config.key_columns
            if column not in dataframe.columns
        ]

        for column in missing_columns:
            issues.append(
                QualityIssue(
                    rule_name=self.name,
                    dataset=dataset,
                    severity=QualitySeverity.CRITICAL,
                    message=f"Uniqueness key column '{column}' is missing from the dataset.",
                    affected_rows=len(dataframe),
                    column=column,
                    metadata={"issue_type": "missing_key_column"},
                )
            )

        if missing_columns:
            return QualityRuleResult(
                rule_name=self.name,
                passed=False,
                issues=tuple(issues),
            )

        key_columns = list(self.config.key_columns)

        if self.config.include_null_keys:
            eligible = dataframe
        else:
            eligible = dataframe.dropna(subset=key_columns)

            if eligible.empty:
                return QualityRuleResult(
                    rule_name=self.name,
                    passed=True,
                    issues=(),
                )

        duplicate_mask = eligible.duplicated(
            subset=key_columns,
            keep=False,
        )

        duplicate_rows = int(duplicate_mask.sum())

        if duplicate_rows == 0:
            return QualityRuleResult(
                rule_name=self.name,
                passed=True,
                issues=(),
            )

        duplicate_groups = int(
            eligible.loc[duplicate_mask, key_columns]
            .drop_duplicates()
            .shape[0]
        )

        issues.append(
            QualityIssue(
                rule_name=self.name,
                dataset=dataset,
                severity=self.config.severity,
                message=(
                    f"Found {duplicate_rows} rows belonging to "
                    f"{duplicate_groups} duplicate key group(s) for "
                    f"{', '.join(key_columns)}."
                ),
                affected_rows=duplicate_rows,
                column=", ".join(key_columns),
                metadata={
                    "issue_type": "duplicate_key",
                    "key_columns": key_columns,
                    "duplicate_groups": duplicate_groups,
                    "duplicate_rows": duplicate_rows,
                    "include_null_keys": self.config.include_null_keys,
                },
            )
        )

        return QualityRuleResult(
            rule_name=self.name,
            passed=False,
            issues=tuple(issues),
        )


def find_duplicate_groups(
    dataframe: pd.DataFrame,
    key_columns: tuple[str, ...],
    include_null_keys: bool = False,
) -> pd.DataFrame:
    missing_columns = [
        column for column in key_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing key columns: {', '.join(missing_columns)}"
        )

    working = dataframe

    if not include_null_keys:
        working = working.dropna(subset=list(key_columns))

    duplicate_mask = working.duplicated(
        subset=list(key_columns),
        keep=False,
    )

    return working.loc[duplicate_mask].copy()