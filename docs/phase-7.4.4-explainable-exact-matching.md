# Phase 7.4.4: Explainable Exact Matching

## Scope

This phase adds privacy-safe, structured evidence to the deterministic exact matcher. It preserves composite-key matching rules and existing matching outcomes while making field completeness, candidate comparisons, and decision reasons inspectable.

## Existing behavior preserved

The matcher continues to:

- Validate configured matching fields.
- Normalize configured values using the Phase 7.3 similarity normalizer.
- Require every configured field for a complete composite key.
- Report incomplete source keys as `no_match` with `missing_matching_value`.
- Report absent exact keys as `no_match` with `no_exact_match`.
- Report duplicate source keys as `review_required` with `duplicate_source_key`.
- Report duplicate target keys as `review_required` with `duplicate_target_key`.
- Prevent a target from being assigned more than once.
- Preserve matching status, method, confidence, field scores, reason, and result ordering.

The explanation work does not introduce fuzzy matching into the exact matcher or alter its matching thresholds.

## Composite-key evidence

A complete exact composite-key match records each configured field as:

- `outcome="exact"`
- `score=1.0`
- `comparable=True`
- `explanation_code="normalized_exact_match"`

This represents normalized equality, not a fuzzy similarity score or calibrated probability.

When a source composite key contains a missing value, evidence is retained for every configured field, including fields appearing after the first missing value. Missing fields use:

- `outcome="missing"`
- `comparable=False`
- `score=None`
- `contribution=None`
- `explanation_code="missing_value"`

Nonmissing fields in an incomplete source key describe normalized key completeness; they must not be interpreted as proof that a target record was compared or matched.

## No-match and exceptional decisions

For a nonempty target dataset with no exact composite-key match, the explanation includes field-level evidence against a deterministically selected candidate. Candidate selection prioritizes the number of normalized exact fields, then the number of comparable fields, then the original target index.

This evidence explains the closest candidate according to those deterministic criteria. It does not change the exact match decision or assert that the candidate satisfies the matching rule.

For an empty target dataset, the explanation explicitly states that no target records are available for comparison. No nonexistent candidate is represented as having been compared.

Duplicate-source-key, duplicate-target-key, and already-assigned-target decisions retain source composite-key evidence. In these branches, the evidence describes normalized key completeness and validity, not a field-by-field comparison against a selected target.

Field-level comparisons do not expose raw source or target values. Missing values are marked as incomparable. Normalized equality and conflict codes describe the comparison result without disclosing record contents.

## Decision evidence

The exact matcher preserves its existing decision vocabulary:

- `missing_matching_value`
- `no_exact_match`
- `duplicate_source_key`
- `duplicate_target_key`
- `target_already_assigned`

Successful exact matches use `decision="matched"` and `rule="exact_composite_key_match"`.

Exact matching does not calculate a fuzzy best-candidate score, second-best score, score gap, threshold, or score contribution. Such values remain unset when they are not part of the exact-matching algorithm.

## Compatibility and integration

`EntityMatch.explanation` remains optional for backward compatibility. Explanation models retain structured field and decision evidence and support serialization through the existing dataclass-based workflow.

Reconciliation workflow results preserve explanations on their match objects. The reconciliation API serializes these explanations in its match response. The explanations are not assumed to be duplicated into each separate reconciliation-result object.

No raw record values are included in explanation evidence.

## Validation

The exact-matcher regression suite covers composite keys, normalization, missing values, no-match explanations, empty target datasets, duplicate keys, target assignment, serialization, and backward-compatible result construction.

Integration regression tests verify that explanations survive the reconciliation orchestrator and are exposed through the API response. Matching-model tests validate model behavior and compatibility.

The current focused verification checkpoint recorded 28 exact-matcher tests, 13 reconciliation API/orchestrator tests, and 24 matching-model tests passing. The complete backend suite is rerun during the Phase 7.4 final audit.

## Related implementation and tests

- `backend/app/services/matching/exact_matcher.py`
- `backend/tests/test_exact_matcher.py`
- `backend/tests/test_reconciliation_api.py`
- `backend/tests/test_reconciliation_orchestrator.py`
- `backend/tests/test_matching_models.py`
- `docs/phase-7.4.2-explanation-models.md`
- `docs/phase-7.4.3-explainable-fuzzy-matching.md`
