from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_valid_csv():
    csv_content = (
        "customer_id,customer_name,email,amount,transaction_date\n"
        "C001,Rahul Kumar,rahul@gmail.com,12500,2026-08-01\n"
        "C002,Prajwal G N,prajwal@gmail.com,18500,2026-08-02\n"
        "C003,Anitha Rao,anitha@gmail.com,9200,2026-08-03\n"
    )

    response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "test_customers.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["original_file_name"] == "test_customers.csv"

    assert data["metadata"]["row_count"] == 3
    assert data["metadata"]["column_count"] == 5

    assert data["quality"]["total_rows"] == 3
    assert data["quality"]["total_columns"] == 5
    assert data["quality"]["missing_cells"] == 0
    assert data["quality"]["duplicate_rows"] == 0
    assert data["quality"]["completeness_percentage"] == 100
    assert data["quality"]["quality_status"] == "PASS"


def test_upload_unsupported_file_type():
    response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "malware.exe",
                BytesIO(b"test content"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_empty_file():
    response = client.post(
        "/datasets/upload",
        files={
            "file": (
                "empty.csv",
                BytesIO(b""),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()