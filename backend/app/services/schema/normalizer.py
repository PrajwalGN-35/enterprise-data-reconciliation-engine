import re


def normalize_column_name(column_name: str) -> str:
    """
    Normalize a column name into a consistent snake_case format.

    Examples:
        "Customer ID"  -> "customer_id"
        "customerId"   -> "customer_id"
        "CUSTOMER-ID"  -> "customer_id"
        "customer id"  -> "customer_id"
    """

    if not isinstance(column_name, str):
        raise TypeError("Column name must be a string.")

    name = column_name.strip()

    # Convert camelCase / PascalCase boundaries to underscores.
    name = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])",
        "_",
        name,
    )

    # Replace spaces and hyphens with underscores.
    name = re.sub(
        r"[\s\-]+",
        "_",
        name,
    )

    # Keep only letters, numbers, and underscores.
    name = re.sub(
        r"[^a-zA-Z0-9_]",
        "",
        name,
    )

    # Convert to lowercase.
    name = name.lower()

    # Collapse repeated underscores.
    name = re.sub(
        r"_+",
        "_",
        name,
    )

    # Remove leading/trailing underscores.
    name = name.strip("_")

    if not name:
        raise ValueError(
            "Column name cannot be empty after normalization."
        )

    return name