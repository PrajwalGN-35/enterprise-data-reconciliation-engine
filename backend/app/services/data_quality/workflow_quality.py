from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from .anomaly import AnomalyConfig, AnomalyRule
from .completeness import CompletenessConfig, CompletenessRule
from .duplicates import DuplicateConfig, DuplicateRule
from .engine import DataQualityEngine
from .persistence import persist_quality_assessment
from .scoring import QualityScoringConfig, score_quality_report


def _numeric_columns(dataframe: pd.DataFrame) -> list[str]:
    columns: list[str] = []
    for column in dataframe.columns:
        if pd.api.types.is_numeric_dtype(dataframe[column]):
            columns.append(str(column))
    return columns


def build_standalone_quality_engine(
    dataframe: pd.DataFrame,
    matching_fields: Iterable[str] = (),
) -> DataQualityEngine:
    """Build the reusable quality engine for standalone API execution.

    Unlike the reconciliation workflow builder, this API-facing builder
    does not require reconciliation matching configuration.
    """
    engine = DataQualityEngine()

    engine.register(
        CompletenessRule(
            CompletenessConfig(
                required_columns=tuple(str(column) for column in dataframe.columns),
                max_null_rate=0.0,
            )
        )
    )

    key_columns = tuple(
        str(column)
        for column in matching_fields
        if str(column) in dataframe.columns
    )

    if key_columns:
        engine.register(
            DuplicateRule(
                DuplicateConfig(
                    key_columns=key_columns,
                    include_null_keys=False,
                )
            )
        )

    anomaly_configs = [
        AnomalyConfig(
            column=column,
            method="iqr",
            threshold=1.5,
            min_samples=5,
        )
        for column in _numeric_columns(dataframe)
    ]

    if anomaly_configs:
        engine.register(AnomalyRule(anomaly_configs))

    return engine


def build_reconciliation_quality_engine(
    dataframe: pd.DataFrame,
    matching_fields: Iterable[str],
) -> DataQualityEngine:
    return build_standalone_quality_engine(
        dataframe=dataframe,
        matching_fields=matching_fields,
    )


def assess_reconciliation_dataset(
    db: Session,
    run_id: str,
    dataframe: pd.DataFrame,
    dataset: str,
    matching_fields: Iterable[str],
    scoring_config: QualityScoringConfig | None = None,
):
    engine = build_reconciliation_quality_engine(
        dataframe=dataframe,
        matching_fields=matching_fields,
    )

    report = engine.run(
        dataframe=dataframe,
        dataset=dataset,
    )

    scored = score_quality_report(
        report,
        scoring_config,
    )

    assessment = persist_quality_assessment(
        db=db,
        run_id=run_id,
        dataset=dataset,
        score=scored["score"],
        risk=scored["risk"],
        rule_count=scored["rule_count"],
        failed_rule_count=scored["failed_rule_count"],
        rule_scores=scored["rules"],
    )

    return assessment, scored
