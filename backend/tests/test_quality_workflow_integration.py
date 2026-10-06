import pandas as pd

from backend.app.services.data_quality.workflow_quality import (
    build_reconciliation_quality_engine,
)
from backend.app.services.data_quality.scoring import QualityRisk


def test_reconciliation_quality_engine_registers_default_rules():
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 2, 4, 5],
            "customer_name": ["A", "B", "B", "D", "E"],
            "amount": [100, 110, 120, 130, 1000],
        }
    )

    engine = build_reconciliation_quality_engine(
        dataframe=dataframe,
        matching_fields=["customer_id"],
    )

    assert len(engine.registry) == 3
    assert {rule.name for rule in engine.registry.all()} == {
        "completeness",
        "uniqueness",
        "statistical_anomaly",
    }


def test_reconciliation_quality_engine_produces_quality_report():
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "amount": [100, 110, 120, 130, 1000],
        }
    )

    engine = build_reconciliation_quality_engine(
        dataframe=dataframe,
        matching_fields=["customer_id"],
    )

    report = engine.run(
        dataframe=dataframe,
        dataset="source.csv",
    )

    assert report.dataset == "source.csv"
    assert report.row_count == 5
    assert report.column_count == 2
    assert report.failed_rules >= 0


def test_reconciliation_quality_engine_handles_non_numeric_dataset():
    dataframe = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C"],
            "name": ["Alpha", "Beta", "Gamma"],
        }
    )

    engine = build_reconciliation_quality_engine(
        dataframe=dataframe,
        matching_fields=["customer_id"],
    )

    assert len(engine.registry) == 2
    assert {rule.name for rule in engine.registry.all()} == {
        "completeness",
        "uniqueness",
    }
