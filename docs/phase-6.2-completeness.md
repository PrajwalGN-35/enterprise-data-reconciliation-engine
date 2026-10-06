# Phase 6.2 — Completeness & Missing-Data Analysis

Phase 6.2 adds the first production-style quality rule to the reusable
Data Quality Engine introduced in Phase 6.1.

## Capabilities

- Required-column validation
- Missing/null value detection
- Blank-string detection
- Configurable maximum null-rate thresholds
- Completeness percentage calculation
- Severity-based quality issues
- Metadata containing null rate and completeness
- Direct integration with DataQualityEngine

## Execution model

Dataset
→ DataQualityEngine
→ CompletenessRule
→ Missing-data analysis
→ QualityIssue
→ DatasetQualityReport

## Design

CompletenessConfig controls:

- equired_columns
- max_null_rate
- lank_strings_are_missing
- issue severity

The rule remains independent from any individual dataset, allowing the
same engine to be reused for CRM, ERP, payment, and future datasets.

## Validation

Phase 6.2 includes isolated unit tests for:

- clean datasets
- missing required columns
- null-rate violations
- blank strings
- configurable thresholds
- completeness calculations
- engine integration