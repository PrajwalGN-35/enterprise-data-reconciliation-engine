import io
import json

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _files(source_content: str, target_content: str):
    return {
        "source_file": (
            "source.csv",
            io.BytesIO(source_content.encode("utf-8")),
            "text/csv",
        ),
        "target_file": (
            "target.csv",
            io.BytesIO(target_content.encode("utf-8")),
            "text/csv",
        ),
    }


def test_reconciliation_api_runs_successfully():
    source = (
        "customer_id,email,amount\n"
        "C001,alice@example.com,1000\n"
        "C002,bob@example.com,2000\n"
    )

    target = (
        "customer_id,email,amount\n"
        "C001,alice@example.com,1000\n"
        "C002,bob@example.com,2000\n"
    )

    response = client.post(
        "/reconciliation/run",
        files=_files(source, target),
        data={
            "matching_fields": json.dumps(["customer_id"]),
            "reconciliation_fields": json.dumps(["email", "amount"]),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["source_file_name"] == "source.csv"
    assert body["target_file_name"] == "target.csv"
    assert body["summary"]["source_record_count"] == 2
    assert body["summary"]["target_record_count"] == 2
    assert body["summary"]["matched_record_count"] == 2
    assert body["summary"]["reconciliation_percentage"] == 100.0


def test_reconciliation_api_reports_discrepancy():
    source = (
        "customer_id,email,amount\n"
        "C001,alice@example.com,1000\n"
    )

    target = (
        "customer_id,email,amount\n"
        "C001,alice@different.com,1000\n"
    )

    response = client.post(
        "/reconciliation/run",
        files=_files(source, target),
        data={
            "matching_fields": json.dumps(["customer_id"]),
            "reconciliation_fields": json.dumps(["email", "amount"]),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["summary"]["discrepancy_record_count"] == 1
    assert body["summary"]["total_discrepancy_count"] == 1
    assert body["summary"]["field_discrepancy_counts"] == {"email": 1}


def test_reconciliation_api_rejects_invalid_matching_fields():
    source = "customer_id,email\nC001,alice@example.com\n"
    target = "customer_id,email\nC001,alice@example.com\n"

    response = client.post(
        "/reconciliation/run",
        files=_files(source, target),
        data={
            "matching_fields": "not-json",
            "reconciliation_fields": json.dumps(["email"]),
        },
    )

    assert response.status_code == 400
    assert "matching_fields must be a valid JSON array" in response.json()["detail"]


def test_reconciliation_api_rejects_unsupported_file_type():
    response = client.post(
        "/reconciliation/run",
        files={
            "source_file": (
                "source.txt",
                io.BytesIO(b"hello"),
                "text/plain",
            ),
            "target_file": (
                "target.csv",
                io.BytesIO(b"customer_id\nC001\n"),
                "text/csv",
            ),
        },
        data={
            "matching_fields": json.dumps(["customer_id"]),
            "reconciliation_fields": json.dumps(["customer_id"]),
        },
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_reconciliation_api_rejects_empty_file():
    response = client.post(
        "/reconciliation/run",
        files={
            "source_file": (
                "source.csv",
                io.BytesIO(b""),
                "text/csv",
            ),
            "target_file": (
                "target.csv",
                io.BytesIO(b"customer_id\nC001\n"),
                "text/csv",
            ),
        },
        data={
            "matching_fields": json.dumps(["customer_id"]),
            "reconciliation_fields": json.dumps(["customer_id"]),
        },
    )

    assert response.status_code == 400
    assert "is empty" in response.json()["detail"]
