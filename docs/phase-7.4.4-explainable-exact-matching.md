# Phase 7.4.4: Explainable Exact Matching

## Scope

This phase adds structured explanations to the existing deterministic exact matcher. It does not redesign composite-key matching, introduce fuzzy similarity, change duplicate handling, or propagate explanations into reconciliation, API schemas, or persistence.

## Existing behavior preserved

The matcher still:

- Validates that configured fields are present, non-empty, and unique.
- Normalizes each configured value through the Phase 7.3 similarity normalizer.
- Requires a complete normalized composite key.
- Rejects incomplete source keys with `missing_matching_value`.
- Reports missing target keys as unavailable for exact lookup.
- Reports duplicate source keys as `review_required` with `duplicate_source_key`.
- Reports duplicate target keys as `review_required` with `duplicate_target_key`.
- Reports absent keys as `no_match` with `no_exact_match`.
- Prevents a target from being assigned more than once.
- Returns the existing `EntityMatch` status, confidence, method, field scores, reason, and result ordering.

## Composite-key evidence

For a successfully matched key, each configured field is represented as `MatchFieldEvidence` with:

- `outcome="exact"`
- `score=1.0`
- `comparable=True`
- `explanation_code="normalized_exact_match"`

This score represents normalized equality for that exact key field. It is not a fuzzy similarity score and is not a calibrated probability.

When composite-key construction encounters a missing value, the reached field is represented as:

- `outcome="missing"`
- `comparable=False`
- `score=None`
- `contribution=None`
- `explanation_code="missing_value"`

Fields after the first missing value are not included because the existing key builder stops at the first incomplete field. This avoids inventing evidence for comparisons that did not occur.

For `no_exact_match`, duplicate-key, and already-assigned-target branches, field evidence is empty because the matcher does not perform a field-by-field comparison against a selected target in those branches. The decision evidence still records the actual control-flow rule.

## Decision evidence

The exact matcher uses the existing decision vocabulary:

- `missing_matching_value`
- `no_exact_match`
- `duplicate_source_key`
- `duplicate_target_key`
- `target_already_assigned`

Successful exact matches have `decision="matched"` and `rule="exact_composite_key_match"`. This stable rule explicitly records that every configured field matched through normalized composite-key equality. Their privacy-safe summary states that all composite-key fields matched exactly.

Exact matching does not calculate a best-candidate score, second-best score, score gap, threshold, or contribution. These values remain unset rather than being fabricated.

## Compatibility and serialization

`EntityMatch.explanation` remains optional, so existing callers can construct results without it. Explanations serialize through the existing `dataclasses.asdict` behavior. Explanations contain field names, outcomes, codes, counts, and summaries only; raw source and target values are not included.

No dependency, database, API, reconciliation, or persistence changes are included in this phase.

## Validation and tests

Focused exact-matching tests cover normalized composite keys, multiple fields, Python and pandas/NumPy missing values, missing evidence validation, no exact matches, duplicate source and target keys, target assignment behavior, serialization, privacy, and backward-compatible `EntityMatch` construction.

Files changed for this phase are `backend/app/services/matching/exact_matcher.py`, `backend/tests/test_exact_matcher.py`, and this documentation file. Existing Phase 7.4.2 and 7.4.3 files remain uncommitted and unchanged by this phase.

The focused command passed with 23 exact-matcher tests:

```text
& .\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_exact_matcher.py -q
23 passed in 0.61s
```

The relevant model and matching suites passed with 113 tests:

```text
& .\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_matching_models.py backend/tests/test_matching_similarity.py backend/tests/test_entity_matcher.py backend/tests/test_candidate_generator.py backend/tests/test_exact_matcher.py -q
113 passed in 1.31s
```

The latest verified complete backend suite passed with 402 tests in 17.52 seconds. One pre-existing Starlette/httpx deprecation warning remains.

The exact-matcher implementation and tests are ready for review. Reconciliation/API propagation and persistence remain deferred work.
