import pytest

from app.services.matching.config import MatchPolicy


def test_default_match_policy_values():
    policy = MatchPolicy()

    assert policy.high_confidence_threshold == 0.90
    assert policy.review_threshold == 0.75
    assert policy.ambiguity_margin == 0.05


def test_match_policy_exports_matcher_keyword_arguments():
    policy = MatchPolicy(
        high_confidence_threshold=0.97,
        review_threshold=0.72,
        ambiguity_margin=0.08,
    )

    assert policy.as_kwargs() == {
        "high_confidence_threshold": 0.97,
        "review_threshold": 0.72,
        "ambiguity_margin": 0.08,
    }


@pytest.mark.parametrize(
    "values",
    [
        {"review_threshold": 0.95, "high_confidence_threshold": 0.80},
        {"review_threshold": -0.1},
        {"high_confidence_threshold": 1.1},
        {"review_threshold": float("nan")},
        {"review_threshold": float("inf")},
        {"high_confidence_threshold": float("-inf")},
        {"review_threshold": True},
        {"high_confidence_threshold": False},
        {"ambiguity_margin": True},
        {"review_threshold": "0.75"},
        {"ambiguity_margin": None},
    ],
)
def test_invalid_match_policy_values_are_rejected(values):
    with pytest.raises(ValueError):
        MatchPolicy(**values)


@pytest.mark.parametrize("value", [0.0, 1.0])
def test_probability_boundaries_are_valid(value):
    policy = MatchPolicy(
        high_confidence_threshold=value,
        review_threshold=value,
        ambiguity_margin=value,
    )

    assert policy.high_confidence_threshold == value
    assert policy.review_threshold == value
    assert policy.ambiguity_margin == value


def test_match_policy_is_immutable():
    policy = MatchPolicy()

    with pytest.raises((AttributeError, TypeError)):
        policy.review_threshold = 0.60