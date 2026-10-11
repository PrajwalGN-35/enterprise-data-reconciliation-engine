# Phase 7.1 - Entity Resolution Architecture and Configuration

## Objective

Establish a validated, reusable policy for entity-resolution decisions before expanding the matching engine in subsequent sub-phases.

## Existing Matching Architecture

The matching service currently includes the following components:

- `candidate_generator.py` - candidate generation support.
- `entity_matcher.py` - entity matching and match decision logic.
- `models.py` - matching-related data models.
- `similarity.py` - similarity calculation support.
- `config.py` - validated matching policy configuration.

The existing matching implementation is retained. This phase establishes a configuration contract without replacing the matching algorithm.

## MatchPolicy

The immutable `MatchPolicy` dataclass centralizes three configuration parameters.

| Parameter | Default | Purpose |
| --- | ---: | --- |
| `high_confidence_threshold` | 0.90 | Minimum configured score threshold for high-confidence matching. |
| `review_threshold` | 0.75 | Minimum configured score threshold for review-level matching. |
| `ambiguity_margin` | 0.05 | Configured score difference used by matching logic to evaluate ambiguity. |

Actual match classification and ambiguity behavior remain the responsibility of the matching implementation.

## Validation Rules

The policy validates all three parameters:

- Values must be real numbers and cannot be booleans.
- Values must be finite.
- Values must fall within the inclusive interval from 0 to 1.
- The review threshold cannot exceed the high-confidence threshold.
- The frozen dataclass prevents ordinary field reassignment after construction.

Invalid configuration raises `ValueError`.

## Matcher Compatibility

`MatchPolicy.as_kwargs()` returns the three configuration values using the keyword names accepted by the existing `match_entities` function.

This provides a consistent configuration interface for subsequent matching integration.

## Testing

The focused test module is:

`backend/tests/test_matching_config.py`

Coverage includes:

- Default policy values.
- Export of matcher-compatible keyword arguments.
- Invalid threshold ordering.
- Negative and above-range values.
- NaN and infinity.
- Boolean, string, and null inputs.
- Inclusive boundary values.
- Immutability.

The full backend regression suite must pass before this phase is committed.

## Scope Boundaries

This phase introduces policy configuration and its tests. It does not claim to complete exact matching, advanced fuzzy matching, explainable scoring, candidate-generation optimization, ambiguity resolution, cross-system integration, reporting, or end-to-end entity-resolution integration. Those remain subsequent Phase 7 deliverables.

## Completion Criteria

- Policy configuration implemented.
- Invalid configuration rejected.
- Focused tests pass.
- Full regression suite passes.
- Documentation added.
- Only intended Phase 7.1 files included in the commit.
