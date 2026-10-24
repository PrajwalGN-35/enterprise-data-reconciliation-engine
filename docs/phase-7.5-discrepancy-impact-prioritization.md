# Phase 7.5: Discrepancy Impact Analysis and Prioritization

## Phase plan

### Evidence and selection

Phase 7.4 already provides privacy-safe explanations for exact and fuzzy entity
matching. The reconciliation layer already produces structured discrepancy
fields, record statuses, and aggregate counts, but it does not rank exceptions
or explain their relative business significance. Quality scoring ranks rules at
the dataset level, not individual reconciliation exceptions.

This phase therefore adds a small, deterministic impact-analysis layer on top
of existing reconciliation results.

### User problem

Operations users can see that records need attention, but cannot reliably
decide which exceptions to investigate first. The new analysis gives each
exception a bounded impact score, priority, and reason codes based on verified
reconciliation facts and configured field criticality.

### Reused modules

- `ReconciliationResult` and `FieldDiscrepancy` from the reconciliation service.
- Existing reconciliation orchestration and API serialization.
- Existing summary validation and status vocabulary.

### Functional requirements

- Calculate a deterministic impact score in `[0.0, 1.0]` for every result.
- Use configurable non-negative field weights and status weights.
- Give missing targets and review-required results a status-based baseline.
- Give discrepancy results the greater of their status baseline and weighted
  discrepant-field coverage.
- Classify scores as `critical`, `high`, `medium`, or `low` using documented
  thresholds and return deterministic priority ordering.
- Return reason codes and field names only; never include source or target
  values.
- Handle empty inputs and reject invalid counts, weights, statuses, or scores.
- Expose the analysis in the reconciliation API response without changing
  matching, reconciliation, or persistence behavior.

### Non-goals

- Monetary or financial impact estimates without supporting business data.
- Automatic source-record changes, remediation, approvals, or human-review
  workflows.
- Historical monitoring, trend storage, dashboards, AI investigation, or new
  database tables.
- Changes to matching decisions, thresholds, discrepancy detection, or quality
  scoring.

### Acceptance criteria

- Impact scores and priority labels are bounded, repeatable, and explainable.
- Missing, review-required, discrepancy, matched, and empty result cases are
  covered by focused tests.
- Invalid configuration and contradictory inputs are rejected explicitly.
- The API includes the impact analysis for existing successful runs while
  retaining the existing response fields and values.
- Privacy tests show that raw discrepancy values are absent from the analysis.
- Focused tests and the complete backend regression suite pass.

## Formula and limitations

For each result, the status baseline is selected from the configured status
weights. For a discrepancy result, field coverage is:

```text
sum(weight for discrepant fields) / sum(weight for compared fields)
```

The result impact is the greater of the baseline and field coverage, bounded
to `[0, 1]`. Fields absent from the configuration use the default field
weight. A missing target or review-required result has no field coverage and
uses only its status baseline. Matched results score `0.0`.

The score is a prioritization heuristic, not a probability, monetary estimate,
or causal diagnosis. Field weights represent supplied business criticality;
they are not inferred from record values.

## Verification

- Focused impact and reconciliation API tests: **12 passed, 2 warnings**.
- Existing reconciliation workflow and API regression tests: **13 passed, 1 warning**.
- Full backend suite: **425 passed, 0 failed, 2 warnings**.
- Full-suite command: `backend\\venv\\Scripts\\python.exe -m pytest backend\\tests -q --basetemp .pytest-tmp-phase-7.5`.
- Warnings are existing Starlette/httpx and AnyIO deprecation warnings from
  the installed test-client dependencies.

The implementation is local and unreleased. No commit, tag, push, database
migration, or source-record mutation was performed.
