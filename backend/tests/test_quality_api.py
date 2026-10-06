import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_data():
    return [
        {
            "customer_id": "C001",
            "customer_name": "Alice",
            "email": "alice@example.com",
            "amount": 1200,
        },
        {
            "customer_id": "C002",
            "customer_name": "Bob",
            "email": "bob@example.com",
            "amount": 1800,
        },
        {
            "customer_id": "C003",
            "customer_name": "Charlie",
            "email": "charlie@example.com",
            "amount": 1500,
        },
    ]


def test_quality_routes_registered():
    paths = app.openapi()["paths"]

    expected = {
        "/quality/profile",
        "/quality/validate",
        "/quality/run",
        "/quality/runs",
        "/quality/runs/{run_id}",
        "/quality/runs/{run_id}/issues",
        "/quality/runs/{run_id}/score",
    }

    assert expected.issubset(paths)


@pytest.mark.parametrize("endpoint", [
    "/quality/profile",
    "/quality/validate",
    "/quality/run",
])
def test_quality_execution_endpoints(client, sample_data, endpoint):
    response = client.post(
        endpoint,
        json={
            "dataset": "customers",
            "data": sample_data,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["dataset"] == "customers"
    assert body["row_count"] == 3
    assert body["column_count"] == 4
    assert body["rule_count"] >= 1
    assert 0 <= body["score"] <= 100
    assert body["risk"] in {
        "EXCELLENT",
        "GOOD",
        "FAIR",
        "POOR",
        "CRITICAL",
    }
    assert isinstance(body["rule_scores"], list)
    assert isinstance(body["issues"], list)


def test_quality_run_with_matching_fields_detects_duplicates(client):
    data = [
        {
            "customer_id": "C001",
            "customer_name": "Alice",
            "amount": 1200,
        },
        {
            "customer_id": "C001",
            "customer_name": "Alice Duplicate",
            "amount": 1300,
        },
    ]

    response = client.post(
        "/quality/run",
        json={
            "dataset": "customers",
            "data": data,
            "matching_fields": ["customer_id"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["rule_count"] >= 2
    assert any(issue["rule"] == "uniqueness" for issue in body["issues"])


def test_quality_run_accepts_empty_data(client):
    response = client.post(
        "/quality/run",
        json={
            "dataset": "empty_dataset",
            "data": [],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["dataset"] == "empty_dataset"
    assert body["row_count"] == 0
    assert body["column_count"] == 0
    assert body["score"] >= 0


def test_quality_run_rejects_empty_dataset_name(client):
    response = client.post(
        "/quality/run",
        json={
            "dataset": "",
            "data": [],
        },
    )

    assert response.status_code == 422


def test_quality_runs_boundary_is_explicit(client):
    response = client.get("/quality/runs")

    assert response.status_code == 200
    assert response.json() == {"runs": []}


@pytest.mark.parametrize(
    "endpoint",
    [
        "/quality/runs/test-run",
        "/quality/runs/test-run/issues",
        "/quality/runs/test-run/score",
    ],
)
def test_quality_persistence_boundary_is_explicit(client, endpoint):
    response = client.get(endpoint)

    assert response.status_code == 501
