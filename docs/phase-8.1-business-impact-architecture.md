# Phase 8.1: Business-Impact Reconciliation Architecture

## Scope and status

Phase 8.1 establishes the architecture and contracts for business-contextual impact analysis. It does not implement business entity mapping, financial calculations, dependency analysis, scoring, new persistence models, or new API endpoints. Subsequent Phase 8 subphases must implement those capabilities behind the boundaries defined here.

The existing Phase 7 reconciliation workflow remains authoritative for schema comparison, normalization, candidate generation, entity matching, ambiguity handling, reconciliation results, data-quality assessment, and deterministic discrepancy prioritization. Phase 7's `DiscrepancyImpactAnalysis` is a reconciliation-exception prioritization result, not a financial or operational exposure estimate.

The repository currently provides local, in-process DataFrame workflows and deterministic synthetic CRM/ERP/payment-system representations. It does not provide live SAP, ERP, CRM, payment-gateway, network, credential, or distributed integrations.

## Existing Phase 7 boundary

The existing workflow is:

```text
CrossSystemDataset
  -> explicit field mapping and normalization
  -> candidate generation and entity matching
  -> ambiguity resolution and reconciliation
  -> Phase 7 discrepancy impact analysis
  -> data-quality assessment
  -> cross-system report generation
  -> report and audit persistence
```

Phase 8 consumes the resulting workflow evidence. It must not re-run matching, replace reconciliation statuses, alter ambiguity policy, or reinterpret Phase 7 scores as monetary values. A future business-impact result is an additional analysis attached to the workflow/report boundary and must remain distinguishable from `impact_analysis`.

## Phase 8 architecture

### Business entity mapping

Maps validated source and target records to business entities such as customer, product, order, invoice, payment, and refund. It owns explicit identifier mapping and entity identity evidence. It does not perform fuzzy matching or silently create identities. A mapping is valid only when supported by explicit identifiers, supplied mappings, validated source data, or documented configuration.

### Business relationship mapping

Represents relationships between mapped entities, for example customer-to-order, order-to-invoice, invoice-to-payment, and order-to-refund. It consumes explicit foreign keys, supplied relationship mappings, validated source data, and documented configuration. Unsupported relationships and inferred dependencies are rejected or marked unavailable; they are never invented.

### Financial discrepancy analysis

Compares authoritative monetary fields after validating amount types, currency identity, sign and status semantics, and calculation basis. It uses `Decimal` for authoritative calculations. It reports observed amount differences and their evidence; it does not decide that a discrepancy is a confirmed loss.

### Missing transaction analysis

Classifies missing source/target transactions using reconciliation evidence and validated relationship context. A missing invoice or payment is an observed discrepancy or potential exposure until the required business evidence confirms a financial loss. Presence or absence alone is not proof of loss.

### Duplicate transaction impact analysis

Identifies duplicate or repeated transaction evidence using explicit transaction identifiers and validated duplicate rules. It attributes exposure to a canonical underlying transaction or exposure group before aggregation so that related invoice, payment, order, and refund records cannot multiply the same exposure.

### Dependency analysis

Determines downstream and upstream business consequences only from validated relationship edges. It reports affected entities and dependency evidence separately from monetary calculations. Missing or unsupported edges reduce confidence or produce an unavailable result; they do not create an inferred dependency.

### Business impact scoring

Combines verified business evidence, exposure classification, relationship scope, and configured business rules into a separate business-impact score. The score is not the Phase 7 discrepancy impact score, is not a probability, and is not an authoritative monetary amount. Inputs, configuration, and score rationale must be retained for reproducibility.

### Severity classification and risk prioritization

Classify the business-impact result using documented thresholds and evidence quality. Severity and priority must retain their rationale, reason codes, and relationship to the underlying exposure. They must not overwrite Phase 7 priority labels.

### Business explanations

Explain the verified evidence, calculation basis, exposure classification, currency, affected entities, reason codes, and uncertainty. Explanations may be generated or formatted by AI in a later phase, but they are advisory text and never authoritative financial calculations.

### Business impact reporting

Adds business-impact content to a future versioned report boundary without changing existing Phase 7 report fields or semantics. Reports must preserve source and target references, entity identifiers, transaction identifiers, calculation evidence, currency, exposure classification, severity, and prioritization rationale.

### Audit integration

Future business-impact persistence must integrate with the existing audit boundary and preserve the atomic report/audit behavior. Audit events must identify the analysis/report, configuration or version used, source references, and outcome status without treating explanation text as financial evidence. New tables or payload fields belong to their implementing phase, not Phase 8.1.

## Financial accuracy rules

1. Authoritative monetary calculations use Python `Decimal`; binary floating point is not permitted for those calculations.
2. Every monetary value has an identifiable currency from validated input or documented configuration. Missing currency is an explicit validation failure or an unavailable financial result.
3. Amounts in different currencies are never aggregated directly. Cross-currency aggregation requires an explicit, versioned exchange-rate basis, rate date, source, and rounding policy.
4. Synthetic data currently generates INR amounts, but INR is a property of that fixture, not a platform default. Existing source-system representations do not universally carry currency columns, so future financial analysis must require currency evidence rather than infer INR.
5. Amounts, currency, scale, sign, transaction status, and calculation basis are retained as evidence. Serialization must not turn a financial calculation into an implicit float-based recalculation.

## Exposure vocabulary

- **Observed discrepancy:** A directly evidenced difference, missing record, duplicate, or invalid relationship in the supplied datasets.
- **Potential financial exposure:** A bounded amount or range that could be affected if the observed discrepancy represents a real business event, with assumptions and uncertainty recorded.
- **Estimated business impact:** A configured estimate combining validated financial and operational consequences. It is not confirmed loss.
- **Confirmed financial loss:** A loss supported by the required authoritative business evidence and confirmation rule. A missing invoice or payment alone never qualifies.

Every result must carry exactly the applicable exposure classification and the evidence needed to move between classifications. Classification changes are explicit and auditable.

## Double-counting safeguards

Exposure attribution is performed at a canonical underlying transaction or exposure-group level. Relationship mapping records edges such as `order_id`, `invoice_id`, `payment_id`, and `refund_id`; attribution then selects a primary exposure owner and records related references. Aggregations operate on unique exposure identities, not on every related row. A payment linked to an invoice linked to an order therefore cannot be counted once per entity. Refunds and reversals reduce or offset the attributed exposure only when their explicit relationship and currency are validated.

Conflicting identifiers, duplicate mappings, missing edges, and cross-currency relationships are surfaced as evidence or validation failures. They are not resolved by unsupported inference.

## Traceability and report contract

Each future business-impact result is designed to retain:

- source and target system, dataset, row, and record references;
- business entity identifiers and relevant transaction identifiers;
- explicit relationship edges and supporting evidence;
- amount, currency, Decimal calculation basis, exchange-rate basis when applicable, and rounding policy;
- exposure classification, assumptions, and evidence quality;
- reason codes, severity, priority, and their rationale;
- analysis/configuration version and audit correlation identifiers.

The existing Phase 7 report continues to expose its existing `summary`, `impact_analysis`, outcomes, quality assessments, and audit behavior. A future business-impact section must be additive and versioned. It must not rename, replace, or merge with `impact_analysis`.

## End-to-end future flow

```text
Phase 7 CrossSystemWorkflowResult
  -> retain ordered source/target references and reconciliation evidence
  -> map business entities from explicit validated identifiers
  -> validate business relationships and dependency edges
  -> validate monetary fields, Decimal values, currencies, and statuses
  -> analyze observed financial, missing, duplicate, and dependency evidence
  -> attribute exposure to unique underlying transactions/groups
  -> classify exposure and calculate separate business-impact score
  -> classify severity and prioritize with rationale
  -> produce evidence-based business explanation
  -> add versioned business-impact report content
  -> persist report and audit event atomically in a later implementation phase
```

## Subphase boundaries

Phase 8.2 through Phase 8.14 should implement one bounded capability at a time: domain contracts and identifiers; relationship validation; monetary normalization; financial discrepancy analysis; missing transactions; duplicate attribution; dependencies; business-impact scoring; severity; risk prioritization; explanations; reporting; audit integration; and final integration/release verification. The exact subphase code must preserve the contracts above and must not introduce live external-system claims without real adapters and tests.

Phase 8.1 intentionally leaves all of these capabilities unimplemented. No financial calculation, entity mapper, dependency engine, scoring algorithm, new database table, or Phase 8 API is introduced here.

## Verification contract

Focused architecture tests verify that the documented Phase 8 boundary matches the current implementation: Phase 7 produces a distinct `impact_analysis`, cross-system reports preserve it unchanged, source/target references remain ordered and traceable, and synthetic relationships/currency fields are explicit fixture facts rather than platform assumptions. Existing Phase 7 impact, integration, reporting, audit, and full-suite tests remain the compatibility gate.
