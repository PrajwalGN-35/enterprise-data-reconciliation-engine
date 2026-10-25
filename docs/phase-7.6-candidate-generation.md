# Phase 7.6: Candidate Generation

## Behavior

`generate_candidates` keeps normalized exact blocking as its default behavior. It can also merge exact blocks from complementary fields and deduplicates each source/target pair, retaining the first configured blocking field as provenance. Candidates are ordered by target position and then blocking-field order.

When a source record has no exact block hit, the generator can use a bounded normalized-prefix fallback. This supports small spelling differences without comparing every source record with every target record. The fallback is opt-in with `fallback_prefix_length`; the default `None` preserves exact-block compatibility. Per-source output can be bounded with `candidate_limit`.

Missing and established missing-token values are excluded from all indexes. Inputs are not mutated. Invalid field names and candidate limits raise `ValueError`.

## Compatibility and limitations

The original three-argument call remains supported and preserves normalized exact matches. The reconciliation workflow now invokes candidate generation across all configured matching fields and passes the resulting target indices to the matcher. A source with no generated candidates falls back to the full target set, preserving recall for missing or unsupported blocking values. The workflow does not apply a candidate limit; direct generator callers may opt into one and own its recall tradeoff. Candidate generation remains separate from similarity scoring and decision classification; the matcher still owns thresholds, ambiguity, explanations, and target reservation. Prefix blocking is a retrieval heuristic, so later phases may add stronger domain-specific indexes when cross-system scale requirements are known.

## Validation

Phase 7.6 tests cover exact blocking, complementary-field deduplication, deterministic ordering, typo-tolerant prefix fallback, missing values, input immutability, invalid configuration, workflow invocation, workflow fallback, and the existing matching contracts.

The reconciliation workflow passes all configured matching fields to candidate generation, uses a three-character prefix fallback, and passes the resulting target indices to `match_entities`. When no candidates are generated for a source record, it deliberately evaluates all targets to preserve recall. Workflow candidate limits are unlimited; direct generator callers remain responsible for the recall tradeoff of an explicit limit.