import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload():
    return {
        "dataset": "customers",
        "data": [
            {"customer_id": "C001", "name": "Alice", "amount": 1000},
            {"customer_id": "C002", "name": "Bob", "amount": 2000},
            {"customer_id": "C003", "name": "Charlie", "amount": 1500},
        ],
    }


def test_quality_run_persists_and_can_be_retrieved():
    response = client.post("/quality/run", json=_payload())
    assert response.status_code == 200

    run = response.json()
    assert run["run_id"]
    run_id = run["run_id"]

    detail = client.get(f"/quality/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["run_id"] == run_id
    assert detail.json()["dataset"] == "customers"

    score = client.get(f"/quality/runs/{run_id}/score")
    assert score.status_code == 200
    assert score.json()["run_id"] == run_id
    assert score.json()["score"] == run["score"]


def test_quality_run_issues_endpoint_returns_list():
    response = client.post(
        "/quality/run",
        json={
            "dataset": "customers",
            "data": [
                {"customer_id": "C001", "name": None, "amount": 1000},
                {"customer_id": "C002", "name": "Bob", "amount": 2000},
            ],
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    issues = client.get(f"/quality/runs/{run_id}/issues")
    assert issues.status_code == 200
    assert isinstance(issues.json(), list)


def test_quality_runs_history_contains_created_run():
    response = client.post("/quality/run", json=_payload())
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    history = client.get("/quality/runs")
    assert history.status_code == 200

    run_ids = [item["run_id"] for item in history.json()["runs"]]
    assert run_id in run_ids


@pytest.mark.parametrize(
    "path",
    [
        "/quality/runs/not-a-real-run",
        "/quality/runs/not-a-real-run/issues",
        "/quality/runs/not-a-real-run/score",
    ],
)
def test_quality_run_not_found(path):
    response = client.get(path)
    assert response.status_code == 404
