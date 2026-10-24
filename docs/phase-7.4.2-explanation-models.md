# Phase 7.4.2: Explanation Models

## Objective

Add backward-compatible structured explanation models for entity-matching results without changing matching behavior.

## Models

- `MatchFieldEvidence` represents one configured field comparison.
- `MatchDecisionEvidence` represents the final decision and the matching rule that supported it.
- `MatchExplanation` groups field evidence and decision evidence.
- `EntityMatch.explanation` optionally carries a `MatchExplanation`.

Field outcomes are controlled as `exact`, `partial`, `conflict`, `missing`, and `not_comparable`. Missing and non-comparable evidence cannot carry a score or contribution, which keeps missing data distinct from a genuine zero-score conflict.

Scores are finite and bounded within `[0.0, 1.0]`. Contributions must be finite. Decision evidence validates known decision statuses, known current decision rules, optional threshold and candidate scores, non-negative comparable-field counts, and consistent score gaps.

## Compatibility

Existing `EntityMatch` fields and constructors remain unchanged. The explanation is optional and defaults to `None`. Existing fuzzy matching, exact matching, reconciliation, API, persistence, threshold, ambiguity, target-uniqueness, and missing-value behavior are unchanged.

The nested dataclasses serialize through the existing `dataclasses.asdict` workflow. No database migration or external dependency is introduced.

## Scope boundaries

This subphase defines and validates the explanation data structures only. Phase 7.4.3 will populate field and decision evidence from the actual fuzzy scoring and decision branches. Exact-matching integration, reconciliation propagation, API schema refinement, and persistence decisions remain subsequent work.
