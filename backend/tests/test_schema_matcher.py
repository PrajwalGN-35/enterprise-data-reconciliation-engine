from app.services.schema.matcher import compare_schemas


def test_compare_schemas_finds_normalized_matches():
    source_columns = [
        "Customer ID",
        "Customer Name",
        "Email",
        "Transaction Date",
    ]

    target_columns = [
        "customerId",
        "customer_name",
        "email",
        "transactionDate",
    ]

    result = compare_schemas(
        source_columns,
        target_columns,
    )

    assert result["matched_columns"] == [
        {
            "source_column": "Customer ID",
            "target_column": "customerId",
            "normalized_name": "customer_id",
            "match_type": "normalized_exact",
        },
        {
            "source_column": "Customer Name",
            "target_column": "customer_name",
            "normalized_name": "customer_name",
            "match_type": "normalized_exact",
        },
        {
            "source_column": "Email",
            "target_column": "email",
            "normalized_name": "email",
            "match_type": "normalized_exact",
        },
        {
            "source_column": "Transaction Date",
            "target_column": "transactionDate",
            "normalized_name": "transaction_date",
            "match_type": "normalized_exact",
        },
    ]

    assert result["summary"] == {
        "source_column_count": 4,
        "target_column_count": 4,
        "matched_column_count": 4,
        "unmatched_source_column_count": 0,
        "unmatched_target_column_count": 0,
        "match_percentage": 100.0,
    }

    assert result["unmatched_source_columns"] == []
    assert result["unmatched_target_columns"] == []


def test_compare_schemas_identifies_unmatched_columns():
    source_columns = [
        "customer_id",
        "amount",
        "transaction_date",
    ]

    target_columns = [
        "customerId",
        "transaction_amount",
        "status",
    ]

    result = compare_schemas(
        source_columns,
        target_columns,
    )

    assert result["matched_columns"] == [
        {
            "source_column": "customer_id",
            "target_column": "customerId",
            "normalized_name": "customer_id",
            "match_type": "normalized_exact",
        }
    ]

    assert result["summary"] == {
        "source_column_count": 3,
        "target_column_count": 3,
        "matched_column_count": 1,
        "unmatched_source_column_count": 2,
        "unmatched_target_column_count": 2,
        "match_percentage": 33.33,
    }

    assert result["unmatched_source_columns"] == [
        "amount",
        "transaction_date",
    ]

    assert result["unmatched_target_columns"] == [
        "transaction_amount",
        "status",
    ]


def test_compare_schemas_with_empty_schemas():
    result = compare_schemas([], [])

    assert result["summary"] == {
        "source_column_count": 0,
        "target_column_count": 0,
        "matched_column_count": 0,
        "unmatched_source_column_count": 0,
        "unmatched_target_column_count": 0,
        "match_percentage": 100.0,
    }

    assert result["matched_columns"] == []
    assert result["unmatched_source_columns"] == []
    assert result["unmatched_target_columns"] == []


def test_compare_schemas_does_not_modify_input_lists():
    source_columns = ["Customer ID", "Email"]
    target_columns = ["customerId", "email"]

    original_source = source_columns.copy()
    original_target = target_columns.copy()

    compare_schemas(
        source_columns,
        target_columns,
    )

    assert source_columns == original_source
    assert target_columns == original_target


def test_compare_schemas_with_different_column_counts():
    source_columns = [
        "customer_id",
        "email",
        "amount",
        "transaction_date",
    ]

    target_columns = [
        "customerId",
        "email",
    ]

    result = compare_schemas(
        source_columns,
        target_columns,
    )

    assert result["summary"] == {
        "source_column_count": 4,
        "target_column_count": 2,
        "matched_column_count": 2,
        "unmatched_source_column_count": 2,
        "unmatched_target_column_count": 0,
        "match_percentage": 50.0,
    }
