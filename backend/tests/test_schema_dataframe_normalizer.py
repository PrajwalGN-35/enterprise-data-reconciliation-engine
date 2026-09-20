import pandas as pd

from app.services.schema.dataframe_normalizer import (
    normalize_dataframe_values,
    normalize_identifier_value,
)


def test_normalize_identifier_preserves_case():
    assert normalize_identifier_value("  CUST-ABC-001  ") == "CUST-ABC-001"


def test_normalize_identifier_missing_marker():
    assert normalize_identifier_value(" NULL ") is None


def test_normalize_dataframe_identifier_values():
    dataframe = pd.DataFrame(
        {
            "customer_id": [
                " CUST-ABC-001 ",
                "cust-xyz-002",
            ]
        }
    )

    normalized = normalize_dataframe_values(
        dataframe,
        column_types={"customer_id": "identifier"},
    )

    assert normalized["customer_id"].tolist() == [
        "CUST-ABC-001",
        "cust-xyz-002",
    ]


def test_normalize_dataframe_column_types():
    dataframe = pd.DataFrame(
        {
            "customer_id": [" C001 "],
            "customer_name": [" Rahul Kumar "],
            "amount": [" 12,500 "],
            "transaction_date": ["08/02/2026"],
        }
    )

    normalized = normalize_dataframe_values(
        dataframe,
        column_types={
            "customer_id": "identifier",
            "customer_name": "text",
            "amount": "numeric",
            "transaction_date": "date",
        },
    )

    assert normalized["customer_id"].iloc[0] == "C001"
    assert normalized["customer_name"].iloc[0] == "rahul kumar"
    assert str(normalized["amount"].iloc[0]) == "12500"
    assert normalized["transaction_date"].iloc[0] == "2026-08-02"


def test_normalize_dataframe_rejects_unknown_type():
    dataframe = pd.DataFrame({"amount": ["100"]})

    try:
        normalize_dataframe_values(
            dataframe,
            column_types={"amount": "unknown"},
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported normalization type" in str(exc)
import pandas as pd
from decimal import Decimal

from app.services.schema.dataframe_normalizer import (
    normalize_dataframe_values,
)
from app.services.schema.value_normalizer import (
    normalize_numeric_value,
    normalize_date_value,
)


def test_numeric_nan_becomes_missing():
    result = normalize_numeric_value(float("nan"))
    assert result is None


def test_dataframe_nan_becomes_missing():
    dataframe = pd.DataFrame(
        {
            "amount": [12500.0, float("nan")],
        }
    )

    normalized = normalize_dataframe_values(
        dataframe,
        column_types={"amount": "numeric"},
    )

    assert str(normalized["amount"].iloc[0]) == "12500.0"
    assert normalized["amount"].iloc[1] is None


def test_numeric_boolean_is_preserved():
    assert normalize_numeric_value(True) is True
    assert normalize_numeric_value(False) is False


def test_numeric_decimal_is_preserved_as_decimal():
    result = normalize_numeric_value(Decimal("12500.50"))

    assert isinstance(result, Decimal)
    assert str(result) == "12500.50"


def test_whitespace_text_becomes_missing():
    dataframe = pd.DataFrame(
        {
            "status": ["   ", " ACTIVE "],
        }
    )

    normalized = normalize_dataframe_values(dataframe)

    assert normalized["status"].iloc[0] is None
    assert normalized["status"].iloc[1] == "active"


def test_date_timestamp_is_normalized():
    timestamp = pd.Timestamp("2026-08-15 14:30:00")

    assert normalize_date_value(timestamp) == "2026-08-15"


def test_unknown_columns_default_to_text():
    dataframe = pd.DataFrame(
        {
            "description": [" Hello World "],
        }
    )

    normalized = normalize_dataframe_values(dataframe)

    assert normalized["description"].iloc[0] == "hello world"
