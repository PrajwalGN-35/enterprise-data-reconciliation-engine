# Phase 6.7 — Data Quality Scoring & Risk Classification

## Objective

Phase 6.7 converts individual data-quality findings into an enterprise
dataset health score.

Earlier phases identify specific quality problems. Phase 6.7 aggregates
those findings into a standardized 0–100 score and an operational risk
classification.

## Capabilities

- 0–100 data-quality score
- Severity-weighted issue impact
- Affected-row impact
- Configurable severity weights
- Configurable risk thresholds
- Rule-level scores
- Failed-rule counts
- Dashboard-ready scoring payload
- Deterministic scoring

## Scoring model

Each issue contributes an impact based on:

`severity weight × affected-row ratio`

Affected-row ratio is capped at `1.0`.

Each rule's total impact is also capped at `1.0`.

The rule score is:

`100 × (1 - rule impact)`

The overall dataset score is the average of all rule scores.

## Default severity weights

| Severity | Weight |
|---|---:|
| INFO | 0.05 |
| WARNING | 0.10 |
| ERROR | 0.20 |
| CRITICAL | 0.40 |

Weights are configurable so different organizations can tune the scoring
model to their governance requirements.

## Risk classification

| Score | Risk |
|---:|---|
| 95–100 | EXCELLENT |
| 85–94.99 | GOOD |
| 70–84.99 | FAIR |
| 50–69.99 | POOR |
| 0–49.99 | CRITICAL |

Thresholds are configurable.

## Enterprise value

Phase 6.7 provides the summary layer required by an enterprise data-quality
dashboard.

Instead of exposing only individual rule failures, downstream systems can
display:

- overall dataset score,
- operational risk,
- failed rule count,
- rule-level scores,
- affected-record counts,
- severity-driven impact.

This establishes the foundation for future monitoring, dashboards,
governance reports, and remediation workflows.

## Separation of responsibilities

- Phase 6.2 — completeness and missing data
- Phase 6.3 — uniqueness and duplicates
- Phase 6.4 — value and format validity
- Phase 6.5 — cross-field and referential integrity
- Phase 6.6 — statistical anomaly detection
- Phase 6.7 — quality scoring and risk classification

Phase 6.7 therefore turns the data-quality engine from a collection of
validation rules into a measurable dataset-health platform.
