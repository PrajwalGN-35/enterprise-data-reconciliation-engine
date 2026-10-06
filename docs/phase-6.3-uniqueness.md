# Phase 6.3 — Uniqueness & Duplicate Detection

Phase 6.3 adds reusable uniqueness and duplicate detection to the
Advanced Data Quality Engine.

## Capabilities

- Business-key duplicate detection
- Composite business-key support
- Duplicate group counting
- Affected-row counting
- Optional inclusion of null key values
- Missing uniqueness-key validation
- Critical severity for missing key columns
- Duplicate-group extraction for downstream investigation
- Direct integration with DataQualityEngine

## Execution model

Dataset
→ DataQualityEngine
→ DuplicateRule
→ Business-key analysis
→ QualityIssue
→ DatasetQualityReport

## Design

DuplicateConfig controls:

- key_columns
- include_null_keys
- issue severity

Completeness and uniqueness remain separate concerns. Completeness identifies
missing key values, while uniqueness determines whether populated keys are
actually unique.

## Duplicate semantics

By default, rows with null values in uniqueness keys are excluded from
duplicate analysis because missing-key quality is handled by the completeness
rule.

When include_null_keys=True, null key values participate in duplicate
detection.

## Validation

Phase 6.3 tests cover:

- unique keys
- duplicate business keys
- composite keys
- null-key behavior
- missing key columns
- duplicate-group extraction
- engine integration
- configuration validation