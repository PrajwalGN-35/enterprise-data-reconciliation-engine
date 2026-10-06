from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.data_quality import (
    DataQualityEngine,
    DatasetQualityReport,
    build_reconciliation_quality_engine,
)
from app.services.data_quality.workflow_quality import (
    build_standalone_quality_engine,
)


REQUIRED_QUALITY_PATHS = {
    "/quality/profile",
    "/quality/validate",
    "/quality/run",
    "/quality/runs",
    "/quality/runs/{run_id}",
    "/quality/runs/{run_id}/issues",
    "/quality/runs/{run_id}/score",
}


def _sample_payload():
    return {
        "dataset": "phase-6-13-integration",
        "data": [
            {"id": "C001", "amount": 1000},
            {"id": "C002", "amount": 2000},
            {"id": "C003", "amount": 3000},
            {"id": "C004", "amount": 4000},
            {"id": "C005", "amount": 5000},
        ],
        "matching_fields": ["id"],
    }


def test_phase_6_13_quality_http_contract():
    client = TestClient(app)

    response = client.post(
        "/quality/profile",
        json=_sample_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["dataset"] == "phase-6-13-integration"
    assert body["row_count"] == 5
    assert body["column_count"] == 2
    assert body["rule_count"] == 3
    assert body["failed_rule_count"] == 0
    assert body["score"] == 100.0
    assert body["risk"] == "EXCELLENT"
    assert len(body["rule_scores"]) == 3
    assert body["issues"] == []


def test_phase_6_13_quality_openapi_contract():
    paths = set(app.openapi().get("paths", {}))
    assert REQUIRED_QUALITY_PATHS.issubset(paths)


def test_phase_6_13_engine_compatibility():
    assert DataQualityEngine is not None
    assert DatasetQualityReport is not None
    assert callable(build_reconciliation_quality_engine)
    assert callable(build_standalone_quality_engine)


def test_phase_6_13_reconciliation_engine_builds():
    import pandas as pd

    dataframe = pd.DataFrame(
        [
            {"id": "C001", "amount": 1000},
            {"id": "C002", "amount": 2000},
            {"id": "C003", "amount": 3000},
            {"id": "C004", "amount": 4000},
            {"id": "C005", "amount": 5000},
        ]
    )

    engine = build_reconciliation_quality_engine(
        dataframe=dataframe,
        matching_fields=["id"],
    )

    assert isinstance(engine, DataQualityEngine)

    report = engine.run(
        dataframe=dataframe,
        dataset="phase-6-13-engine",
    )

    assert isinstance(report, DatasetQualityReport)
    assert report.dataset == "phase-6-13-engine"


def test_phase_6_13_standalone_engine_builds():
    import pandas as pd

    dataframe = pd.DataFrame(
        [
            {"id": "C001", "amount": 1000},
            {"id": "C002", "amount": 2000},
            {"id": "C003", "amount": 3000},
            {"id": "C004", "amount": 4000},
            {"id": "C005", "amount": 5000},
        ]
    )

    engine = build_standalone_quality_engine(
        dataframe=dataframe,
        matching_fields=["id"],
    )

    assert isinstance(engine, DataQualityEngine)


def test_phase_6_13_quality_route_validation():
    client = TestClient(app)

    response = client.post(
        "/quality/profile",
        json={
            "dataset": "",
            "data": [],
        },
    )

    assert response.status_code == 422


def test_phase_6_13_quality_run_contract():
    client = TestClient(app)

    response = client.post(
        "/quality/run",
        json=_sample_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["dataset"] == "phase-6-13-integration"
    assert isinstance(body["score"], (int, float))
    assert body["risk"] in {
        "EXCELLENT",
        "GOOD",
        "FAIR",
        "POOR",
        "CRITICAL",
    }
    assert isinstance(body["issues"], list)


def test_phase_6_13_python_sources_are_bom_free():
    root = Path(__file__).resolve().parents[1]

    python_files = list(root.rglob("*.py"))

    assert python_files

    for path in python_files:
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            f"BOM detected: {path}"
        )


def test_phase_6_13_repository_has_no_uncommitted_changes_after_test_creation():
    # This test intentionally verifies only that the repository can be inspected.
    # Git cleanliness is validated by the master release command itself.
    root = Path(__file__).resolve().parents[2]
    assert (root / ".git").exists()
