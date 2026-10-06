from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .engine import QualityIssue, QualityRuleResult, QualitySeverity


@dataclass(frozen=True)
class AnomalyConfig:
    column: str
    method: str = "iqr"
    threshold: float = 1.5
    severity: QualitySeverity = QualitySeverity.WARNING
    allow_null: bool = True
    min_samples: int = 5

    def __post_init__(self) -> None:
        allowed_methods = {"iqr", "zscore"}

        if not self.column:
            raise ValueError("column must not be empty")

        if self.method not in allowed_methods:
            raise ValueError(
                f"method must be one of: {', '.join(sorted(allowed_methods))}"
            )

        if self.threshold <= 0:
            raise ValueError("threshold must be greater than zero")

        if self.min_samples < 2:
            raise ValueError("min_samples must be at least 2")


class AnomalyRule:
    name = "statistical_anomaly"

    def __init__(self, configs: Iterable[AnomalyConfig]) -> None:
        self.configs = tuple(configs)

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        dataset: str,
    ) -> QualityRuleResult:
        issues: list[QualityIssue] = []

        for config in self.configs:
            if config.column not in dataframe.columns:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=QualitySeverity.CRITICAL,
                        message=(
                            f"Required anomaly-analysis column "
                            f"'{config.column}' is missing."
                        ),
                        affected_rows=len(dataframe),
                        column=config.column,
                        metadata={
                            "issue_type": "missing_column",
                            "column": config.column,
                            "method": config.method,
                        },
                    )
                )
                continue

            series = pd.to_numeric(
                dataframe[config.column],
                errors="coerce",
            )

            if not config.allow_null and series.isna().any():
                null_count = int(series.isna().sum())

                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=config.severity,
                        message=(
                            f"'{config.column}' contains null or "
                            "non-numeric values."
                        ),
                        affected_rows=null_count,
                        column=config.column,
                        metadata={
                            "issue_type": "invalid_numeric_value",
                            "column": config.column,
                            "method": config.method,
                            "invalid_rows": null_count,
                        },
                    )
                )

            valid_values = series.dropna()

            if len(valid_values) < config.min_samples:
                continue

            if config.method == "iqr":
                q1 = float(valid_values.quantile(0.25))
                q3 = float(valid_values.quantile(0.75))
                iqr = q3 - q1

                lower_bound = q1 - (config.threshold * iqr)
                upper_bound = q3 + (config.threshold * iqr)

                anomaly_mask = (
                    series.lt(lower_bound)
                    | series.gt(upper_bound)
                )

                method_metadata = {
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                }

            else:
                mean = float(valid_values.mean())
                std = float(valid_values.std(ddof=0))

                if std == 0:
                    continue

                z_scores = (series - mean).abs() / std
                anomaly_mask = z_scores.gt(config.threshold)

                method_metadata = {
                    "mean": mean,
                    "std": std,
                    "z_score_threshold": config.threshold,
                }

            anomaly_mask = anomaly_mask.fillna(False)
            anomaly_count = int(anomaly_mask.sum())

            if anomaly_count:
                issues.append(
                    QualityIssue(
                        rule_name=self.name,
                        dataset=dataset,
                        severity=config.severity,
                        message=(
                            f"'{config.column}' contains "
                            f"{anomaly_count} statistical anomaly "
                            f"record(s) using {config.method.upper()} detection."
                        ),
                        affected_rows=anomaly_count,
                        column=config.column,
                        metadata={
                            "issue_type": "statistical_anomaly",
                            "column": config.column,
                            "method": config.method,
                            "threshold": config.threshold,
                            "sample_size": len(valid_values),
                            "allow_null": config.allow_null,
                            "min_samples": config.min_samples,
                            "anomaly_rows": anomaly_count,
                            **method_metadata,
                        },
                    )
                )

        return QualityRuleResult(
            rule_name=self.name,
            passed=not issues,
            issues=tuple(issues),
        )


def detect_iqr_outliers(
    series: pd.Series,
    threshold: float = 1.5,
) -> pd.Series:
    if threshold <= 0:
        raise ValueError("threshold must be greater than zero")

    numeric = pd.to_numeric(series, errors="coerce")

    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - threshold * iqr
    upper_bound = q3 + threshold * iqr

    return (
        (numeric < lower_bound)
        | (numeric > upper_bound)
    ).fillna(False)


def detect_zscore_anomalies(
    series: pd.Series,
    threshold: float = 3.0,
) -> pd.Series:
    if threshold <= 0:
        raise ValueError("threshold must be greater than zero")

    numeric = pd.to_numeric(series, errors="coerce")

    mean = numeric.mean()
    std = numeric.std(ddof=0)

    if pd.isna(std) or std == 0:
        return pd.Series(False, index=series.index)

    z_scores = (numeric - mean).abs() / std

    return z_scores.gt(threshold).fillna(False)
