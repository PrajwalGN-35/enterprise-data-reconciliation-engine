# Phase 7.8: Cross-System Integration

## Architecture

`CrossSystemDataset` is an independently callable adapter boundary, not a replacement for the existing upload API. It carries a system name, dataset name, DataFrame, optional external-to-canonical field mapping, and optional record identifier field. `run_cross_system_reconciliation` copies and maps both inputs, then invokes the existing `run_reconciliation_workflow`; it does not duplicate matching, candidate generation, ambiguity resolution, reconciliation, summary, or impact logic. The legacy `/reconciliation/run` endpoint intentionally remains on its existing upload, persistence, quality-assessment, and audit path; API-level mapping metadata is deferred to a future interface decision.

Mappings are applied before the existing deterministic column normalization. Column labels must be strings. Missing mapped columns, duplicate normalized columns, invalid metadata, missing record identifiers, incompatible matching fields, and invalid workflow configuration raise `CrossSystemIntegrationError`, a `ValueError` subtype. Empty DataFrames are accepted and produce an empty structured result.

## Traceability and behavior

The result retains source and target system/dataset metadata and returns ordered record references containing an explicit `role` (`source` or `target`), each original record index, and the configured external identifier. `record_id_field` is an optional external/business identifier: null and duplicate values are allowed because row index plus role is the stable record reference. The wrapper never sorts, filters, or deduplicates records. Input DataFrames are copied and are not mutated. The existing workflow performs candidate generation, uses its recall-preserving fallback, applies fuzzy scoring and Phase 7.7 ambiguity policy, enforces one-to-one target assignment, and produces the existing reconciliation summary and impact analysis.

This phase provides a reusable in-process boundary for uploaded, registered, or adapter-supplied DataFrames. No live SAP, ERP, CRM, payment gateway, credentials, network connector, or external service is introduced; tests use deterministic synthetic DataFrames.

## Limitations and validation

Mappings are explicit dictionaries rather than inferred semantic mappings. The wrapper does not persist connector metadata or create database tables, and it does not implement global assignment optimization. The normal upload API does not yet expose this boundary's metadata or mapping inputs. Cross-system integration tests cover compatible differently shaped datasets, identifier preservation, explicit source/target roles, null and duplicate business identifiers, non-string labels, real workflow execution, input immutability, empty inputs, malformed mappings, incompatible schemas, and error handling. Phase 7.9 reporting and audit extensions remain out of scope.