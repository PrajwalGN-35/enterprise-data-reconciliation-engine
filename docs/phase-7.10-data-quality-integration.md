# Phase 7.10: Data-Quality Integration

Phase 7.10 integrates the existing deterministic data-quality engine with the independently callable cross-system reconciliation boundary.

`run_cross_system_reconciliation` now runs the existing reconciliation quality engine and scorer independently for the mapped source and target DataFrames. The resulting `quality_assessments` dictionary is keyed by `source` and `target` and contains the existing dataset, score, risk, rule count, failed-rule count, and rule-level scores. These findings are informational and are included in Phase 7.9 reports; they do not override match confidence, ambiguity status, reconciliation status, or discrepancy-impact scoring.

Quality assessment uses canonical mapped DataFrames and the configured matching fields. Quality failures propagate explicitly rather than being converted into match decisions or silently ignored. Persistence of quality assessments remains the existing legacy API responsibility; the cross-system adapter does not create a competing database write path.

## Validation

Tests cover quality snapshots alongside matched/discrepant reconciliation, preservation of distinct matching and impact semantics, and explicit quality-engine failure handling. Existing quality, matching, reconciliation, reporting, persistence, and API tests remain part of the regression suite.

## Scope boundaries

No new quality thresholds, universal score, global optimizer, live external connector, or quality-driven automatic match override was introduced. Later performance and release phases remain separate.
