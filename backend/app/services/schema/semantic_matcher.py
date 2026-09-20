from app.services.schema.normalizer import normalize_column_name


SEMANTIC_ALIASES = {
    "id": {"id", "identifier", "key"},
    "customer_id": {
        "customer_id",
        "customer_identifier",
        "customer_key",
        "client_id",
        "client_identifier",
    },
    "name": {"name", "full_name", "customer_name", "client_name"},
    "email": {"email", "email_address", "email_id"},
    "amount": {
        "amount",
        "transaction_amount",
        "total_amount",
        "payment_amount",
        "value",
    },
    "transaction_date": {
        "transaction_date",
        "transaction_datetime",
        "transaction_timestamp",
        "transaction_time",
    },
}


def get_semantic_group(column_name: str) -> str | None:
    normalized_name = normalize_column_name(column_name)

    for group_name, aliases in SEMANTIC_ALIASES.items():
        if normalized_name in aliases:
            return group_name

    return None


def find_semantic_matches(
    source_columns: list[str],
    target_columns: list[str],
) -> list[dict]:
    """
    Identify potential semantic relationships between
    otherwise-unmatched source and target columns.

    Semantic matches are suggestions, not confirmed matches.
    """

    source_groups = {
        column: get_semantic_group(column)
        for column in source_columns
    }

    target_groups = {
        column: get_semantic_group(column)
        for column in target_columns
    }

    matches = []

    for source_column, source_group in source_groups.items():
        if source_group is None:
            continue

        for target_column, target_group in target_groups.items():
            if source_group != target_group:
                continue

            if normalize_column_name(source_column) == normalize_column_name(
                target_column
            ):
                continue

            matches.append(
                {
                    "source_column": source_column,
                    "target_column": target_column,
                    "semantic_group": source_group,
                    "match_type": "potential_semantic",
                }
            )

    return matches
