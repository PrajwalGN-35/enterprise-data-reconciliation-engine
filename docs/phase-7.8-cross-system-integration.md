# Phase 7.8: Cross-System Integration

## Architecture

`CrossSystemDataset` is the integration boundary for independently supplied system data. It carries a system name, dataset name, DataFrame, optional external-to-canonical field mapping, and optional record identifier field. `run_cross_system_reconciliation` copies and maps both inputs, then invokes the existing `run_reconciliation_workflow`; it does not duplicate matching, candidate generation, ambiguity resolution, reconciliation, summary, or impact logic.

Mappings are applied before the existing deterministic column normalization. Missing mapped columns, duplicate normalized columns, invalid metadata, missing record identifiers, incompatible matching fields, and invalid workflow configuration raise `CrossSystemIntegrationError`, a `ValueError` subtype. Empty DataFrames are accepted and produce an empty structured result.

## Traceability and behavior

The result retains source and target system/dataset metadata and returns ordered record references containing each original record index and configured external identifier. Input DataFrames are copied and are not mutated. The existing workflow performs candidate generation, uses its recall-preserving fallback, applies fuzzy scoring and Phase 7.7 ambiguity policy, enforces one-to-one target assignment, and produces the existing reconciliation summary and impact analysis.

This phase provides a reusable in-process boundary for uploaded, registered, or adapter-supplied DataFrames. No live SAP, ERP, CRM, payment gateway, credentials, network connector, or external service is introduced; tests use deterministic synthetic DataFrames.

## Limitations and validation

Mappings are explicit dictionaries rather than inferred semantic mappings. The wrapper does not persist connector metadata or create database tables, and it does not implement global assignment optimization. Cross-system integration tests cover compatible differently shaped datasets, identifier preservation, real workflow execution, input immutability, empty inputs, malformed mappings, incompatible schemas, and error handling. Phase 7.9 reporting and audit extensions remain out of scope.