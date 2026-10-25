# Phase 7.11: Regression and Performance Hardening

## Regression coverage

Phase 7.11 adds larger deterministic cross-system coverage while preserving the existing matching and reporting algorithms. The regression tests verify 100 source rows against 100 reversed target rows, one-to-one assignment, stable source/target row references, and safe empty inputs with quality integration.

Existing Phase 7.9 tests cover malformed report payloads, invalid indexes, non-finite serialization values, unsupported objects, persistence rollback, audit consistency, and retrieval errors. Existing Phase 7.10 tests cover quality scoring alongside matching and impact analysis plus explicit quality-engine failure propagation.

## Performance evidence

The current hot path uses indexed candidate generation for populated blocking fields and a deliberate full-target fallback when no candidates are generated. No benchmark or SLA exists in the repository, so no optimization threshold is asserted. A reproducible local measurement on the current environment processed 1,000 source and 1,000 target synthetic customer rows in approximately 0.081534 seconds, producing 1,000 matches. This is an observation, not a production capacity guarantee.

The phase does not add caching, concurrency, global assignment, or speculative optimization. Future performance work should measure representative datasets and memory usage before changing these semantics.

## Limitations

The benchmark uses deterministic synthetic in-memory DataFrames and does not measure database persistence, API transport, external connectors, or production hardware. Windows pytest temporary-directory cleanup remains an environment consideration; verification uses unique repository-local temporary directories when needed.
