import pytest

from app.services.matching.exact_matcher import match_entities_exact


def test_matches_normalized_composite_key():
    source = [
        {
            "customer_id": " CUST-001 ",
            "email": "Rahul@Example.com",
        }
    ]
    target = [
        {
            "customer_id": "cust-001",
            "email": "rahul@example.com",
        }
    ]

    result = match_entities_exact(
        source, target, ["customer_id", "email"]
    )

    assert len(result) == 1
    assert result[0].status == "matched"
    assert result[0].method == "exact"
    assert result[0].target_index == 0
    assert result[0].confidence == 1.0
    assert result[0].field_scores == {
        "customer_id": 1.0,
        "email": 1.0,
    }
    assert result[0].reason is None


def test_requires_every_composite_key_field_to_match():
    source = [{"customer_id": "CUST-001", "email": "a@example.com"}]
    target = [{"customer_id": "CUST-001", "email": "b@example.com"}]

    result = match_entities_exact(
        source, target, ["customer_id", "email"]
    )

    assert result[0].status == "no_match"
    assert result[0].reason == "no_exact_match"
    assert result[0].target_index is None


@pytest.mark.parametrize("missing", [None, "", " ", "NA", "N/A", "null", "None"])
def test_missing_composite_key_value_never_matches(missing):
    source = [{"customer_id": "CUST-001", "email": missing}]
    target = [{"customer_id": "CUST-001", "email": missing}]

    result = match_entities_exact(
        source, target, ["customer_id", "email"]
    )

    assert result[0].status == "no_match"
    assert result[0].reason == "missing_matching_value"
    assert result[0].target_index is None


def test_reports_duplicate_source_keys_for_review():
    source = [
        {"id": "A-1", "email": "a@example.com"},
        {"id": "a-1", "email": "A@example.com"},
    ]
    target = [{"id": "A-1", "email": "a@example.com"}]

    result = match_entities_exact(source, target, ["id", "email"])

    assert len(result) == 2
    assert all(item.status == "review_required" for item in result)
    assert all(item.reason == "duplicate_source_key" for item in result)
    assert all(item.target_index is None for item in result)


def test_reports_duplicate_target_keys_for_review():
    source = [{"id": "A-1", "email": "a@example.com"}]
    target = [
        {"id": "A-1", "email": "a@example.com"},
        {"id": "a-1", "email": "A@example.com"},
    ]

    result = match_entities_exact(source, target, ["id", "email"])

    assert result[0].status == "review_required"
    assert result[0].reason == "duplicate_target_key"
    assert result[0].target_index is None


def test_matches_independent_records_one_to_one():
    source = [
        {"id": "A-1", "email": "a@example.com"},
        {"id": "B-2", "email": "b@example.com"},
    ]
    target = [
        {"id": "B-2", "email": "b@example.com"},
        {"id": "A-1", "email": "a@example.com"},
    ]

    result = match_entities_exact(source, target, ["id", "email"])

    assert [item.target_index for item in result] == [1, 0]
    assert all(item.status == "matched" for item in result)
    assert len({item.target_index for item in result}) == len(result)


def test_unmatched_source_does_not_consume_target():
    source = [
        {"id": "UNKNOWN", "email": "unknown@example.com"},
        {"id": "A-1", "email": "a@example.com"},
    ]
    target = [{"id": "A-1", "email": "a@example.com"}]

    result = match_entities_exact(source, target, ["id", "email"])

    assert result[0].status == "no_match"
    assert result[1].status == "matched"
    assert result[1].target_index == 0


def test_empty_source_returns_empty_results():
    assert match_entities_exact(
        [], [{"id": "A-1"}], ["id"]
    ) == []


def test_empty_target_returns_no_matches():
    result = match_entities_exact([{"id": "A-1"}], [], ["id"])

    assert len(result) == 1
    assert result[0].status == "no_match"
    assert result[0].reason == "no_exact_match"


@pytest.mark.parametrize("fields", [[], [" "], ["id", ""]])
def test_rejects_invalid_matching_fields(fields):
    with pytest.raises(ValueError):
        match_entities_exact([{"id": "A-1"}], [], fields)


def test_rejects_duplicate_matching_fields():
    with pytest.raises(ValueError, match="must not contain duplicates"):
        match_entities_exact(
            [{"id": "A-1"}], [{"id": "A-1"}], ["id", "id"]
        )


def test_missing_record_field_is_not_an_exact_match():
    result = match_entities_exact(
        [{"id": "A-1"}],
        [{"other_id": "A-1"}],
        ["id"],
    )

    assert result[0].status == "no_match"
    assert result[0].reason == "no_exact_match"


def test_numeric_and_string_keys_follow_existing_normalization():
    result = match_entities_exact(
        [{"id": 123}],
        [{"id": "123"}],
        ["id"],
    )

    assert result[0].status == "matched"
    assert result[0].target_index == 0