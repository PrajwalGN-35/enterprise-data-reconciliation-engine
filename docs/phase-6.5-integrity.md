# Phase 6.5 — Cross-Field & Referential Integrity

## Objective

Phase 6.5 extends the advanced data-quality engine from individual-value
validation into relationship-level validation.

### Capabilities

- Cross-field comparisons
- Conditional field requirements
- Referential integrity and orphan detection
- Critical missing-column handling
- Configurable severity
- Null-handling controls
- Row-level affected-record reporting
- Structured rule metadata

## Cross-field integrity

Examples:

- `start_date <= end_date`
- `minimum_amount <= maximum_amount`
- `quantity > 0` through a related field comparison
- two fields must be equal or different

Supported operators:

`eq`, `ne`, `lt`, `le`, `gt`, `ge`

## Conditional requirements

A field can become mandatory based on another field.

Example:

`status = active` → `email` must be populated.

This complements Phase 6.2 completeness checks by allowing requiredness
to depend on business context.

## Referential integrity

The engine detects child values that do not exist in a reference column.

Example:

`customer_id` must exist in the known customer identifier set.

This identifies orphan records before downstream reconciliation or reporting.

## Separation of responsibilities

- Phase 6.2 — completeness and missing values
- Phase 6.3 — uniqueness and duplicates
- Phase 6.4 — value/format/range validity
- Phase 6.5 — relationships between fields and records

Phase 6.5 therefore moves the quality engine toward enterprise business-rule
validation rather than treating every column independently.
