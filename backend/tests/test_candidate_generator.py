import numpy as np
import pandas as pd
import pytest

from app.services.matching.candidate_generator import (
    generate_candidates,
)


def test_candidate_generation():
    source = [
        {"customer_id": "C001"},
        {"customer_id": "C002"},
    ]

    target = [
        {"customer_id": "c001"},
        {"customer_id": "C003"},
    ]

    candidates = generate_candidates(
        source,
        target,
        "customer_id",
    )

    assert len(candidates) == 1
    assert candidates[0].source_index == 0
    assert candidates[0].target_index == 0


def test_candidate_generation_excludes_missing_values():
    source = [
        {"email": None},
        {"email": "rahul@gmail.com"},
    ]

    target = [
        {"email": None},
        {"email": "RAHUL@GMAIL.COM"},
    ]

    candidates = generate_candidates(
        source,
        target,
        "email",
    )

    assert len(candidates) == 1


@pytest.mark.parametrize(
    ("source_missing", "target_missing"),
    [
        (None, pd.NA),
        (pd.NA, pd.NA),
        (pd.NaT, np.datetime64("NaT", "ns")),
        (float("nan"), None),
    ],
)
def test_candidate_generation_excludes_all_missing_representations(
    source_missing,
    target_missing,
):
    candidates = generate_candidates(
        [{"customer_id": source_missing}],
        [{"customer_id": target_missing}],
        "customer_id",
    )

    assert candidates == []


def test_duplicate_target_values_produce_multiple_candidates():
    source = [
        {"name": "Rahul Kumar"},
    ]

    target = [
        {"name": "rahul kumar"},
        {"name": "RAHUL KUMAR"},
    ]

    candidates = generate_candidates(
        source,
        target,
        "name",
    )

    assert len(candidates) == 2


def test_complementary_blocking_fields_are_deduplicated_and_ordered():
    candidates = generate_candidates(
        [{"customer_id": "C001", "email": "person@example.com"}],
        [
            {"customer_id": "c001", "email": "other@example.com"},
            {"customer_id": "c002", "email": "PERSON@EXAMPLE.COM"},
        ],
        "customer_id",
        blocking_fields=["email"],
    )

    assert [(item.target_index, item.field) for item in candidates] == [
        (0, "customer_id"),
        (1, "email"),
    ]


def test_candidates_found_by_multiple_blocks_are_emitted_once():
    candidates = generate_candidates(
        [{"customer_id": "C001", "email": "person@example.com"}],
        [{"customer_id": "c001", "email": "PERSON@EXAMPLE.COM"}],
        "customer_id",
        blocking_fields=["email"],
    )

    assert len(candidates) == 1
    assert candidates[0].field == "customer_id"


def test_prefix_fallback_retrieves_typo_tolerant_candidates():
    candidates = generate_candidates(
        [{"name": "Rahul Kumar"}],
        [{"name": "Rahul Kumer"}],
        "name",
        fallback_prefix_length=3,
    )

    assert [(item.source_index, item.target_index) for item in candidates] == [
        (0, 0),
    ]


def test_prefix_fallback_does_not_use_missing_values_or_mutate_inputs():
    source = [{"name": None}]
    target = [{"name": None}, {"name": "Rahul Kumar"}]

    assert generate_candidates(source, target, "name") == []
    assert source == [{"name": None}]
    assert target == [{"name": None}, {"name": "Rahul Kumar"}]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fallback_prefix_length": 0},
        {"candidate_limit": 0},
        {"blocking_fields": [""]},
    ],
)
def test_invalid_candidate_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        generate_candidates([{"name": "Rahul"}], [{"name": "Rahul"}], "name", **kwargs)
