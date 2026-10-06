# Phase 6.8 — Quality Score Persistence & Audit Integration

## Objective

Persist data-quality assessment results against reconciliation runs so that
quality scores, risk classifications, rule-level scores, and historical
assessments can be retrieved through the reconciliation API.

## Architecture

Dataset
  -> Quality Rules
  -> Quality Issues
  -> Quality Score
  -> Risk Classification
  -> QualityAssessment
  -> ReconciliationRun
  -> API History / Audit Context

## Persistence Model

Table: `quality_assessments`

Fields:

- `id` — primary key
- `run_id` — foreign key to `reconciliation_runs.id`
- `dataset` — assessed dataset identifier
- `score` — quality score from 0 to 100
- `risk` — quality risk classification
- `rule_count` — total evaluated rules
- `failed_rule_count` — failed rule count
- `rule_scores` — serialized rule-level scoring details
- `created_at` — assessment creation timestamp

## Service Layer

`backend/app/services/data_quality/persistence.py`

Provides:

- `persist_quality_assessment`
- `get_quality_assessment`
- `get_quality_assessments`

`backend/app/services/data_quality/reconciliation_quality.py`

Provides reconciliation-oriented wrappers for:

- recording quality assessments
- retrieving the latest assessment
- retrieving assessment history

## API

### Latest Quality Assessment

`GET /reconciliation/runs/{run_id}/quality`

Returns the latest quality assessment associated with a reconciliation run.

### Quality Assessment History

`GET /reconciliation/runs/{run_id}/quality/history`

Returns historical quality assessments associated with a reconciliation run.

## API Response

Quality assessment responses expose:

- assessment ID
- reconciliation run ID
- dataset
- score
- risk
- rule count
- failed rule count
- rule-level scores
- creation timestamp

## Engineering Principles

Phase 6.8 deliberately uses a dedicated `quality_assessments` table instead
of expanding `reconciliation_runs` with multiple quality-specific columns.

This keeps reconciliation execution metadata separate from quality-assessment
history and supports future quality trend analysis.

The implementation is deterministic, test-covered, and designed to provide
dashboard-ready quality assessment data.

## Verification

Phase 6.8 Master Command 4 verification:

- Targeted Phase 6.8 tests: 12 passed
- Full regression suite: 244 passed
- Git diff validation: clean

Existing Starlette/httpx deprecation warning remains non-blocking and does not
affect test success.

## Scope Boundary

The current phase establishes quality-assessment persistence, service
integration, retrieval APIs, and historical storage.

Automatic invocation of quality scoring from the live reconciliation execution
workflow can be introduced as a subsequent integration enhancement once the
quality-assessment input contract is finalized.
