# Phase 6.6 — Statistical Anomaly & Outlier Detection

## Objective

Phase 6.6 extends the advanced data-quality engine beyond structural,
format, completeness, uniqueness, and relationship validation into
statistical data-quality analysis.

The goal is to identify values that are technically valid but statistically
unusual and therefore potentially suspicious.

## Capabilities

- IQR-based outlier detection
- Z-score anomaly detection
- Configurable thresholds
- Minimum sample-size protection
- Configurable severity
- Null handling
- Numeric conversion validation
- Structured anomaly metadata
- DataQualityEngine integration

## IQR detection

For a numeric column:

- Q1 = 25th percentile
- Q3 = 75th percentile
- IQR = Q3 - Q1
- Lower bound = Q1 - threshold × IQR
- Upper bound = Q3 + threshold × IQR

Values outside those bounds are reported as statistical anomalies.

The default threshold is `1.5`.

## Z-score detection

Z-score detection measures how far a value is from the dataset mean:

`z = |value - mean| / standard deviation`

Values above the configured threshold are reported as anomalies.

The default threshold is `3.0`.

## Enterprise value

Phase 6.6 catches a different class of data-quality problem than earlier
phases.

A value may be:

- present,
- unique,
- correctly formatted,
- within its declared data type,
- and still statistically suspicious.

Examples include:

- unusually large transaction amounts,
- abnormal quantities,
- unexpected account balances,
- extreme processing times,
- unusual operational measurements.

## Separation of responsibilities

- Phase 6.2 — completeness and missing data
- Phase 6.3 — uniqueness and duplicates
- Phase 6.4 — value and format validity
- Phase 6.5 — cross-field and referential integrity
- Phase 6.6 — statistical anomaly and outlier detection

Phase 6.6 therefore adds behavioral/statistical validation to the
enterprise data-quality foundation.
