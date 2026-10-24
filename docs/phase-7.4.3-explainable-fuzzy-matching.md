# Phase 7.4.3: Explainable Fuzzy Matching

## Objective

Populate the Phase 7.4.2 explanation models from the existing fuzzy matcher without changing matching policy, score aggregation, missing-value handling, or target assignment.

## Field evidence

The fuzzy matcher emits one `MatchFieldEvidence` item for each configured field on the selected candidate. Missing values on either side are represented as `missing` with `comparable=False`, no score, and no contribution. Populated values are classified as:

- `exact`: normalized values compare at `1.0`.
- `partial`: populated values receive a score greater than `0.0` and less than `1.0`.
- `conflict`: populated values receive a score of `0.0`.

Stable explanation codes are:

- `missing_value`
- `normalized_exact_match`
- `fuzzy_partial_match`
- `populated_conflict`

No raw source or target values are included in explanations.

## Aggregation and contributions

The existing fuzzy score remains the arithmetic mean of comparable field scores:

```text
combined_score = sum(comparable field scores) / number of comparable fields
```

The existing bounded, four-decimal score is preserved. Each comparable field contribution is calculated from the same denominator:

```text
field contribution = field score / number of comparable fields
```

Missing fields are excluded from both the denominator and contribution total. The explanation therefore reflects the existing missing-aware aggregation policy. Contributions are not treated as calibrated probabilities.

## Decision evidence

Decision evidence is created directly in the existing matcher branches:

- `no_candidate`: no positive-score candidate remained eligible. A diagnostic score and field evidence are included only when an evaluated candidate exists; otherwise they remain absent.
- `ambiguity_margin`: the best and second-best eligible candidate scores are available, so the explanation includes both scores, their gap, and the configured ambiguity margin.
- `high_confidence_threshold`: the candidate met the configured high-confidence threshold.
- `review_threshold`: the candidate did not meet the configured review threshold.

A candidate meeting the review threshold but not the high-confidence threshold retains the existing `confidence_below_auto_match_threshold` reason and uses the high-confidence threshold as the decision threshold. Existing statuses, reasons, candidate ordering, ambiguity precedence, and target uniqueness are unchanged.

## Privacy and scope

Explanations contain field names, outcomes, scores, codes, counts, thresholds, and privacy-safe summaries only. They do not contain raw customer or business values.

This phase does not integrate explanations into exact matching, reconciliation results, API schemas, persistence, or database models. Those remain Phase 7.4.4 or later work.

## Validation

Focused matching and explanation-model tests cover field outcomes, missing representations, contributions, thresholds, ambiguity, candidate availability, privacy, target uniqueness, nested model validation, and backward-compatible `EntityMatch` serialization. The latest verified full backend suite passes with 402 tests and one pre-existing Starlette/httpx deprecation warning (17.52 seconds).

## Known limitation

`EntityMatch` exposes evidence for the selected candidate, or the strongest evaluated diagnostic candidate when no eligible candidate exists. It does not yet expose a collection of explanations for every rejected candidate. A later phase can extend the result contract if per-candidate audit history is required.
