# Phase 7.9: Cross-System Reporting and Auditability

## Scope

Phase 7.9 adds a reporting boundary over the existing `CrossSystemWorkflowResult`. It does not change entity matching, candidate generation, ambiguity policy, reconciliation, or the legacy upload endpoint.

## Report contract

Reports use schema version `7.9.1` and contain:

- A UUID report identifier.
- UTC `generated_at` timestamps serialized as ISO-8601 strings.
- Source and target system/dataset metadata.
- Existing schema comparison, summary, and impact-analysis objects.
- Source and target record references.
- Per-source outcomes containing the original match and reconciliation objects.
- Stable report-level counts.

The report builder validates that source and target references, match indexes, and reconciliation indexes preserve the workflow's zero-based execution-local row convention. A null target index remains unassigned. An ordinary review-required result may retain a target reference; an ambiguity result retains no target reference when the matcher returns `None`.

## Serialization and persistence

The serializer recursively supports dataclasses, enums, tuples, dictionaries with string keys, UUIDs, dates/datetimes, Decimal values, NumPy scalars, pandas missing values, lists, and ordinary JSON primitives. Missing values become JSON `null`; timestamps use UTC ISO-8601 strings. Non-finite numbers and unsupported objects raise explicit errors, and payloads pass `json.dumps(..., allow_nan=False)`.

`CrossSystemReport` stores metadata and the JSON payload in a portable SQLAlchemy `Text` column. The model is registered through the existing `app.models` registry and `db_init.py`; this repository has no migration framework and uses the established `Base.metadata.create_all(bind=engine)` initialization approach. No database artifact or external dependency is added.

`persist_cross_system_report` adds the report and `cross_system_report_persisted` audit event to the same SQLAlchemy session and commits them atomically. Any commit failure rolls back the transaction and propagates the original database error. Audit details contain report metadata, not the full payload.

## Retrieval boundary

`GET /reconciliation/reports/{report_id}` validates UUID identifiers, returns the stored JSON-compatible report, returns `404` when absent, returns `400` for malformed identifiers, and returns `500` when a stored payload is corrupted. The existing upload, reconciliation history, quality, persistence, and audit endpoints remain unchanged.

## Security and limitations

The report contains workflow evidence and discrepancy values supplied by the existing reconciliation result. It does not add credentials, connector access, or live SAP/ERP/CRM/payment integrations. The adapter remains independently callable, mapping metadata is explicit, report metadata is not persisted into reconciliation runs, and global assignment optimization remains out of scope. Future phases may add richer report queries or API report creation without changing the core matcher.

## Validation

Focused tests cover matched, discrepancy, missing-target, ambiguous, ordinary review-required, empty, null/duplicate identifier, traceability, serialization, non-finite values, unsupported objects, persistence, audit creation, rollback, retrieval, malformed IDs, corrupted payloads, and existing reconciliation history compatibility. The final verification record is maintained in the Phase 7.9 checkpoint report.
