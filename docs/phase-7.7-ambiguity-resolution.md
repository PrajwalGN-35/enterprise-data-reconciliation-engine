# Phase 7.7: Ambiguity Resolution

## Policy

The fuzzy matcher ranks eligible candidates by descending score and uses target position as a stable presentation tie-breaker. The tie-breaker does not decide an unresolved business tie. When the best and runner-up scores differ by less than the configured `ambiguity_margin`, the result is `review_required` with no target assignment, including when the best score meets the high-confidence threshold.

The ambiguity explanation includes the best score, runner-up score, configured margin, and calculated score gap. A clearly separated candidate continues through the existing high-confidence, review, and no-match thresholds.

## Uniqueness and reservation

Existing source-order greedy assignment is preserved. Matched and ordinary review-required results reserve their selected target as before. An ambiguity result has `target_index=None` and does not reserve either candidate, so unresolved ambiguity cannot consume a target or create a duplicate assignment. Exact matching safeguards remain unchanged.

## Limitations and validation

This phase does not introduce global assignment optimization. Source-order effects remain an explicit limitation for competing source records. Tests cover high-confidence near-ties, equal-score determinism, score-gap evidence, ambiguity explanations, target uniqueness, reservation behavior, exact matching protections, and existing candidate-generation contracts.