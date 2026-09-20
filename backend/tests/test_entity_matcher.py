from app.services.matching.entity_matcher import (
    match_entities,
)


def test_high_confidence_match():
    source = [
        {
            "name": "Prajwal G N",
            "email": "prajwal@gmail.com",
        }
    ]

    target = [
        {
            "name": "Prajwal G. N",
            "email": "PRAJWAL@GMAIL.COM",
        }
    ]

    results = match_entities(
        source,
        target,
        fields=["name", "email"],
    )

    assert len(results) == 1
    assert results[0].status == "matched"
    assert results[0].target_index == 0
    assert results[0].confidence >= 0.90


def test_moderate_match_requires_review():
    source = [
        {"name": "Rahul Kumar"}
    ]

    target = [
        {"name": "Rahul K"}
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
        high_confidence_threshold=0.95,
        review_threshold=0.70,
    )

    assert results[0].status == "review_required"
    assert results[0].target_index == 0
    assert results[0].reason == (
        "confidence_below_auto_match_threshold"
    )


def test_low_confidence_is_not_matched():
    source = [
        {"name": "Rahul Kumar"}
    ]

    target = [
        {"name": "Anitha Rao"}
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
        high_confidence_threshold=0.90,
        review_threshold=0.80,
    )

    assert results[0].status == "no_match"
    assert results[0].target_index is None


def test_ambiguous_candidates_require_review():
    source = [
        {"name": "Rahul Kumar"}
    ]

    target = [
        {"name": "Rahul K"},
        {"name": "Rahul Kumar S"},
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
        high_confidence_threshold=0.98,
        review_threshold=0.70,
        ambiguity_margin=0.20,
    )

    assert results[0].status == "review_required"
    assert results[0].target_index is None
    assert results[0].reason == "ambiguous_candidates"


def test_target_is_used_only_once():
    source = [
        {"name": "Rahul Kumar"},
        {"name": "Rahul Kumar"},
    ]

    target = [
        {"name": "Rahul Kumar"},
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
    )

    matched = [
        result
        for result in results
        if result.status == "matched"
    ]

    assert len(matched) == 1
    assert results[1].status == "no_match"
    assert results[1].target_index is None


def test_missing_values_do_not_create_matches():
    source = [
        {"name": None}
    ]

    target = [
        {"name": None}
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
    )

    assert results[0].status == "no_match"
    assert results[0].target_index is None


def test_invalid_thresholds_are_rejected():
    source = [{"name": "Rahul"}]
    target = [{"name": "Rahul"}]

    try:
        match_entities(
            source,
            target,
            fields=["name"],
            review_threshold=0.95,
            high_confidence_threshold=0.80,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for invalid thresholds."
        )
