# Enterprise Data Reconciliation Engine

An enterprise-style data quality and cross-system reconciliation platform designed to identify structural differences, normalize heterogeneous datasets, match entities, detect field-level discrepancies, and produce reconciliation metrics through a tested FastAPI workflow.

## Phase 3 — Core Reconciliation Engine

Phase 3 implements the complete reconciliation pipeline:

- Dataset ingestion and profiling
- Schema normalization and comparison
- Semantic column matching
- Data value normalization
- Fuzzy entity matching
- Field-level discrepancy detection
- Reconciliation summary metrics
- End-to-end workflow orchestration
- FastAPI reconciliation API
- Automated unit and API-level testing

### Reconciliation Workflow

Source Dataset + Target Dataset
→ Schema Comparison
→ Column Normalization
→ Value Normalization
→ Entity Matching
→ Field Reconciliation
→ Exception Detection
→ Summary & Metrics
→ API Response

### API

`POST /reconciliation/run`

The endpoint accepts source and target CSV, XLSX, or JSON datasets together with configurable matching and reconciliation fields.

### Technology

- Python
- FastAPI
- Pandas
- RapidFuzz
- Pytest
- Data quality validation
- Schema intelligence
- Entity resolution
- Reconciliation analytics
- API testing

### Test Status

Phase 3 currently passes:

**95 automated tests**

The tests cover data-processing services, schema handling, entity matching, reconciliation logic, workflow orchestration, API behavior, validation, and regression scenarios.

## Recruiter Summary

Built an enterprise-style data reconciliation engine that combines schema intelligence, data normalization, fuzzy entity resolution, field-level discrepancy detection, and automated reconciliation analytics into a tested FastAPI workflow.
