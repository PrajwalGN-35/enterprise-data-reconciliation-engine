import pandas as pd

from app.services.schema.transformer import normalize_dataframe_columns


def test_normalize_dataframe_columns():
    dataframe = pd.DataFrame(
        columns=[
            "Customer ID",
            "customerName",
            "EMAIL-ADDRESS",
            "Transaction Amount",
        ]
    )

    normalized = normalize_dataframe_columns(dataframe)

    assert list(normalized.columns) == [
        "customer_id",
        "customer_name",
        "email_address",
        "transaction_amount",
    ]


def test_normalize_dataframe_columns_preserves_data():
    dataframe = pd.DataFrame(
        {
            "Customer ID": ["C001", "C002"],
            "Customer Name": ["Rahul", "Anitha"],
        }
    )

    normalized = normalize_dataframe_columns(dataframe)

    assert list(normalized.columns) == [
        "customer_id",
        "customer_name",
    ]

    assert normalized["customer_id"].tolist() == [
        "C001",
        "C002",
    ]

    assert normalized["customer_name"].tolist() == [
        "Rahul",
        "Anitha",
    ]


def test_normalize_dataframe_columns_does_not_modify_original():
    dataframe = pd.DataFrame(
        {
            "Customer ID": ["C001"],
            "Customer Name": ["Rahul"],
        }
    )

    normalize_dataframe_columns(dataframe)

    assert list(dataframe.columns) == [
        "Customer ID",
        "Customer Name",
    ]
