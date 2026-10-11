"""Validated configuration policies for entity resolution."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real


def _validate_probability(name: str, value: float) -> None:
    """Require a finite, non-boolean real number in the closed interval [0, 1]."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number between 0 and 1.")

    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1.")


@dataclass(frozen=True)
class MatchPolicy:
    """Decision thresholds used by the entity-resolution engine."""

    high_confidence_threshold: float = 0.90
    review_threshold: float = 0.75
    ambiguity_margin: float = 0.05

    def __post_init__(self) -> None:
        _validate_probability(
            "review_threshold", self.review_threshold
        )
        _validate_probability(
            "high_confidence_threshold",
            self.high_confidence_threshold,
        )
        _validate_probability("ambiguity_margin", self.ambiguity_margin)

        if self.review_threshold > self.high_confidence_threshold:
            raise ValueError(
                "Thresholds must satisfy "
                "0 <= review_threshold <= high_confidence_threshold <= 1."
            )

    def as_kwargs(self) -> dict[str, float]:
        """Return policy values in the existing matcher keyword format."""
        return {
            "high_confidence_threshold": self.high_confidence_threshold,
            "review_threshold": self.review_threshold,
            "ambiguity_margin": self.ambiguity_margin,
        }