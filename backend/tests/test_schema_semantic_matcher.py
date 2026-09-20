from app.services.schema.semantic_matcher import find_semantic_matches


def test_find_semantic_match_for_amount():
    result = find_semantic_matches(
        ["amount"],
        ["transaction_amount"],
    )

    assert result == [
        {
            "source_column": "amount",
            "target_column": "transaction_amount",
            "semantic_group": "amount",
            "match_type": "potential_semantic",
        }
    ]


def test_find_semantic_match_for_email():
    result = find_semantic_matches(
        ["email"],
        ["email_address"],
    )

    assert result == [
        {
            "source_column": "email",
            "target_column": "email_address",
            "semantic_group": "email",
            "match_type": "potential_semantic",
        }
    ]


def test_find_semantic_match_for_customer_id():
    result = find_semantic_matches(
        ["customer_id"],
        ["customer_identifier"],
    )

    assert result == [
        {
            "source_column": "customer_id",
            "target_column": "customer_identifier",
            "semantic_group": "customer_id",
            "match_type": "potential_semantic",
        }
    ]


def test_exact_normalized_names_are_not_semantic_matches():
    result = find_semantic_matches(
        ["customer_id"],
        ["customer_id"],
    )

    assert result == []


def test_unrelated_columns_are_not_matched():
    result = find_semantic_matches(
        ["amount"],
        ["status"],
    )

    assert result == []


def test_multiple_semantic_matches():
    result = find_semantic_matches(
        ["amount", "email", "customer_id"],
        [
            "transaction_amount",
            "email_address",
            "customer_identifier",
        ],
    )

    assert result == [
        {
            "source_column": "amount",
            "target_column": "transaction_amount",
            "semantic_group": "amount",
            "match_type": "potential_semantic",
        },
        {
            "source_column": "email",
            "target_column": "email_address",
            "semantic_group": "email",
            "match_type": "potential_semantic",
        },
        {
            "source_column": "customer_id",
            "target_column": "customer_identifier",
            "semantic_group": "customer_id",
            "match_type": "potential_semantic",
        },
    ]
