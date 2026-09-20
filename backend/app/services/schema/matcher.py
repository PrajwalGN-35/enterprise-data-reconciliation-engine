from app.services.schema.normalizer import normalize_column_name
from app.services.schema.semantic_matcher import find_semantic_matches


def compare_schemas(
    source_columns: list[str],
    target_columns: list[str],
) -> dict:
    """
    Compare two dataset schemas using deterministic matching
    followed by semantic potential matching.

    Matching order:
    1. Normalized exact match
    2. Potential semantic match

    Semantic matches are suggestions and are not counted
    as confirmed matches.
    """

    source_normalized = {
        column: normalize_column_name(column)
        for column in source_columns
    }

    target_normalized = {
        column: normalize_column_name(column)
        for column in target_columns
    }

    source_by_normalized = {
        normalized: original
        for original, normalized in source_normalized.items()
    }

    target_by_normalized = {
        normalized: original
        for original, normalized in target_normalized.items()
    }

    matched_columns = []

    for normalized_name in source_by_normalized:
        if normalized_name in target_by_normalized:
            matched_columns.append(
                {
                    "source_column": source_by_normalized[
                        normalized_name
                    ],
                    "target_column": target_by_normalized[
                        normalized_name
                    ],
                    "normalized_name": normalized_name,
                    "match_type": "normalized_exact",
                }
            )

    matched_source_columns = {
        match["source_column"]
        for match in matched_columns
    }

    matched_target_columns = {
        match["target_column"]
        for match in matched_columns
    }

    unmatched_source_columns = [
        column
        for column in source_columns
        if column not in matched_source_columns
    ]

    unmatched_target_columns = [
        column
        for column in target_columns
        if column not in matched_target_columns
    ]

    potential_matches = find_semantic_matches(
        unmatched_source_columns,
        unmatched_target_columns,
    )

    total_source_columns = len(source_columns)
    total_target_columns = len(target_columns)
    matched_count = len(matched_columns)

    comparison_base = max(
        total_source_columns,
        total_target_columns,
    )

    match_percentage = (
        (matched_count / comparison_base) * 100
        if comparison_base > 0
        else 100.0
    )

    return {
        "summary": {
            "source_column_count": total_source_columns,
            "target_column_count": total_target_columns,
            "matched_column_count": matched_count,
            "potential_match_count": len(potential_matches),
            "unmatched_source_column_count": len(
                unmatched_source_columns
            ),
            "unmatched_target_column_count": len(
                unmatched_target_columns
            ),
            "match_percentage": round(
                match_percentage,
                2,
            ),
        },
        "matched_columns": matched_columns,
        "potential_matches": potential_matches,
        "unmatched_source_columns": unmatched_source_columns,
        "unmatched_target_columns": unmatched_target_columns,
    }
