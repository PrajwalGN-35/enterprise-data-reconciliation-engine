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
