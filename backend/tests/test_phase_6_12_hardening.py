from pathlib import Path
import ast
import importlib

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]


def _client():
    from app.main import app
    return TestClient(app)


def _sample_rows():
    return [
        {
            "customer_id": "C001",
            "customer_name": "Alice",
            "email": "alice@example.com",
            "amount": 1000,
            "transaction_date": "2026-01-01",
        },
        {
            "customer_id": "C002",
            "customer_name": "Bob",
            "email": "bob@example.com",
            "amount": 2000,
            "transaction_date": "2026-01-02",
        },
        {
            "customer_id": "C003",
            "customer_name": "Charlie",
            "email": "charlie@example.com",
            "amount": 3000,
            "transaction_date": "2026-01-03",
        },
    ]


def test_required_quality_routes_are_registered():
    client = _client()

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    expected = {
        "/quality/profile": "post",
        "/quality/validate": "post",
        "/quality/run": "post",
        "/quality/runs": "get",
        "/quality/runs/{run_id}": "get",
        "/quality/runs/{run_id}/issues": "get",
        "/quality/runs/{run_id}/score": "get",
    }

    for path, method in expected.items():
        assert path in paths
        assert method in paths[path]


def test_quality_schemas_import_cleanly():
    module = importlib.import_module("app.api.quality_schemas")

    required = [
        "QualityIssueResponse",
        "QualityRuleResultResponse",
        "QualityRunResponse",
        "QualityProfileRequest",
        "QualityValidateRequest",
        "QualityRunRequest",
        "QualityRunListItem",
        "QualityRunListResponse",
    ]

    for name in required:
        assert hasattr(module, name)


def test_invalid_quality_payload_is_rejected():
    client = _client()

    response = client.post(
        "/quality/run",
        json={
            "dataset": "",
            "data": _sample_rows(),
            "matching_fields": [],
        },
    )

    assert response.status_code == 422


def test_missing_required_payload_is_rejected():
    client = _client()

    response = client.post(
        "/quality/run",
        json={
            "dataset": "hardening-test",
        },
    )

    assert response.status_code == 422


def test_quality_run_returns_stable_contract():
    client = _client()

    response = client.post(
        "/quality/run",
        json={
            "dataset": "phase-6-12-contract",
            "data": _sample_rows(),
            "matching_fields": ["customer_id"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    required = {
        "dataset",
        "row_count",
        "column_count",
        "rule_count",
        "failed_rule_count",
        "score",
        "risk",
        "rule_scores",
        "issues",
    }

    assert required.issubset(body)
    assert body["dataset"] == "phase-6-12-contract"
    assert body["row_count"] == 3
    assert body["column_count"] == 5
    assert 0 <= body["score"] <= 100
    assert isinstance(body["risk"], str)
    assert isinstance(body["rule_scores"], list)
    assert isinstance(body["issues"], list)


def test_quality_run_persists_and_is_retrievable():
    client = _client()

    response = client.post(
        "/quality/run",
        json={
            "dataset": "phase-6-12-persistence",
            "data": _sample_rows(),
            "matching_fields": ["customer_id"],
        },
    )

    assert response.status_code == 200

    runs = client.get("/quality/runs")

    assert runs.status_code == 200

    matching = [
        item
        for item in runs.json().get("runs", [])
        if item.get("dataset") == "phase-6-12-persistence"
    ]

    assert matching

    run_id = matching[-1]["run_id"]

    detail = client.get(f"/quality/runs/{run_id}")
    issues = client.get(f"/quality/runs/{run_id}/issues")
    score = client.get(f"/quality/runs/{run_id}/score")

    assert detail.status_code == 200
    assert issues.status_code == 200
    assert score.status_code == 200


def test_nonexistent_run_has_consistent_404_contract():
    client = _client()

    for path in [
        "/quality/runs/phase-6-12-does-not-exist",
        "/quality/runs/phase-6-12-does-not-exist/issues",
        "/quality/runs/phase-6-12-does-not-exist/score",
    ]:
        response = client.get(path)
        assert response.status_code == 404


def test_engine_modules_import_cleanly():
    modules = [
        "app.services.data_quality.workflow_quality",
        "app.services.data_quality.persistence",
        "app.services.data_quality.quality_run_persistence",
        "app.services.data_quality.scoring",
        "app.models.quality_run",
    ]

    for module_name in modules:
        importlib.import_module(module_name)


def test_reconciliation_quality_compatibility_exists():
    module = importlib.import_module(
        "app.services.data_quality.workflow_quality"
    )

    assert hasattr(module, "build_standalone_quality_engine")
    assert hasattr(module, "build_reconciliation_quality_engine")


def test_python_sources_are_utf8_and_bom_free():
    targets = [
        ROOT / "backend" / "app",
        ROOT / "backend" / "tests",
    ]

    checked = 0

    for base in targets:
        for path in base.rglob("*.py"):
            raw = path.read_bytes()

            assert not raw.startswith(b"\xef\xbb\xbf"), (
                f"UTF-8 BOM detected in {path}"
            )

            source = raw.decode("utf-8")
            ast.parse(source, filename=str(path))

            checked += 1

    assert checked > 0


def test_quality_scoring_is_deterministic():
    import pandas as pd

    from app.services.data_quality.scoring import score_quality_report
    from app.services.data_quality.workflow_quality import (
        build_standalone_quality_engine,
    )

    dataframe = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "customer_name": "Alice",
                "email": "alice@example.com",
                "amount": 1000,
                "transaction_date": "2026-01-01",
            },
            {
                "customer_id": "C002",
                "customer_name": "Bob",
                "email": "bob@example.com",
                "amount": 2000,
                "transaction_date": "2026-01-02",
            },
            {
                "customer_id": "C003",
                "customer_name": "Charlie",
                "email": "charlie@example.com",
                "amount": 3000,
                "transaction_date": "2026-01-03",
            },
        ]
    )

    engine = build_standalone_quality_engine(
        dataframe=dataframe,
        matching_fields=["customer_id"],
    )

    report = engine.run(
        dataframe=dataframe,
        dataset="determinism-test",
    )

    first = score_quality_report(report)
    second = score_quality_report(report)

    assert first == second
    assert first["dataset"] == "determinism-test"
    assert 0 <= first["score"] <= 100


def test_read_only_quality_endpoint():
    client = _client()

    response = client.get("/quality/runs")

    assert response.status_code == 200


def test_wrong_http_method_is_rejected():
    client = _client()

    for path in [
        "/quality/profile",
        "/quality/validate",
        "/quality/run",
    ]:
        response = client.get(path)
        assert response.status_code in {405, 422}