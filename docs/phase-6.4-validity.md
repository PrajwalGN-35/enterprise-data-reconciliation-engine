# Phase 6.4 â€” Validity & Format Quality Rules

Phase 6.4 adds reusable validity and format validation to the Advanced Data
Quality Engine.

## Capabilities

- Email format validation
- Regex/pattern validation
- Numeric range validation
- Date validity validation
- Optional null handling
- Missing-column detection
- Critical severity for missing columns
- Configurable issue severity
- Direct integration with DataQualityEngine
- Reusable boolean validation helper

## Execution model

Dataset
â†’ DataQualityEngine
â†’ ValidityRule
â†’ Format/value validation
â†’ QualityIssue
â†’ DatasetQualityReport

## Design

ValidityConfig controls:

- target column
- validator type
- severity
- null handling
- regex pattern
- numeric minimum
- numeric maximum

Supported validators:

- email
- egex
-
umeric_range
- date

## Separation of responsibilities

Phase 6.2 handles completeness and missing values.

Phase 6.3 handles uniqueness and duplicate business keys.

Phase 6.4 handles whether populated values conform to expected
format/type/range rules.

This separation prevents different data-quality dimensions from becoming
coupled.

## Validation

Phase 6.4 tests cover:

- valid email values
- invalid email values
- regex validation
- numeric ranges
- non-numeric values
- date validation
- nullable values
- non-nullable values
- missing columns
- engine integration
- reusable validation helper
- configuration validation