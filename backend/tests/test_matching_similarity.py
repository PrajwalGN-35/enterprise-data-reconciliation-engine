from app.services.matching.similarity import (
    calculate_similarity,
    normalize_for_similarity,
)


def test_similarity_exact_match():
    assert calculate_similarity(
        "Rahul Kumar",
        "Rahul Kumar",
    ) == 1.0


def test_similarity_case_difference():
    assert calculate_similarity(
        "rahul@gmail.com",
        "RAHUL@GMAIL.COM",
    ) == 1.0


def test_similarity_missing_values():
    assert calculate_similarity(
        None,
        "Rahul Kumar",
    ) == 0.0


def test_normalize_for_similarity():
    assert normalize_for_similarity(
        "  Rahul Kumar  "
    ) == "rahul kumar"


def test_similarity_name_variation():
    score = calculate_similarity(
        "Prajwal G N",
        "Prajwal G. N",
    )

    assert 0.0 <= score <= 1.0
    assert score > 0.8
