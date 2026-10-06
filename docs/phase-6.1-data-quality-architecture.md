# Phase 6.1 — Advanced Data Quality Engine Architecture

Introduces the reusable architecture for the Advanced Data Quality Engine.

```text
Dataset → DataQualityEngine → QualityRuleRegistry → Quality Rules
                                      ↓
                              QualityRuleResult
                                      ↓
                             DatasetQualityReport
```

Future Phase 6 sub-phases add completeness, uniqueness, validity, referential-integrity, consistency, anomaly, and scoring rules through this architecture.
