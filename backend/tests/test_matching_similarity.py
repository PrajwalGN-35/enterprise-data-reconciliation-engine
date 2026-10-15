import math

import numpy as np
import pandas as pd
import pytest

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


@pytest.mark.parametrize(
    "missing",
    [
        None,
        float("nan"),
        np.float64("nan"),
        pd.NA,
        pd.NaT,
        np.datetime64("NaT", "ns"),
        "",
        "N/A",
        "null",
        "None",
    ],
)
def test_similarity_missing_values_score_zero(missing):
    assert calculate_similarity(missing, "Rahul Kumar") == 0.0


@pytest.mark.parametrize(
    "missing",
    [
        None,
        float("nan"),
        np.float64("nan"),
        pd.NA,
        pd.NaT,
        np.datetime64("NaT", "ns"),
    ],
)
def test_missing_values_normalize_to_empty(missing):
    assert normalize_for_similarity(missing) == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  Rahul\t Kumar\n", "rahul kumar"),
        ("ＲＡＨＵＬ　ＫＵＭＡＲ", "rahul kumar"),
        ("Cafe\u0301", "café"),
        (123, "123"),
        (0, "0"),
        (False, "false"),
    ],
)
def test_normalize_for_similarity_handles_unicode_whitespace_and_values(
    value,
    expected,
):
    assert normalize_for_similarity(value) == expected


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


def test_similarity_numeric_and_string_values_match_exactly():
    assert calculate_similarity(123, "123") == 1.0


@pytest.mark.parametrize(
    ("source", "target"),
    [("North America", "NA Business Unit"), ("none of the above", "None")],
)
def test_missing_tokens_only_match_as_exact_standalone_values(source, target):
    assert calculate_similarity(source, target) < 1.0


def test_similarity_scores_are_finite_and_bounded():
    for source, target in [(None, "x"), ("x", "x"), ("x", "y")]:
        score = calculate_similarity(source, target)

        assert math.isfinite(score)
        assert 0.0 <= score <= 1.0
