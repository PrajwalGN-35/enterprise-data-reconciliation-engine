# Enterprise Automated Data Quality & Cross-System Reconciliation Engine

An enterprise-style **data trust and cross-system reconciliation platform** designed to identify, explain, and track data inconsistencies across CRM, ERP, payment, and other business systems.

Built with **Python, FastAPI, Pandas, RapidFuzz, PostgreSQL, SQLAlchemy, and Pytest**, the platform combines automated data-quality validation, entity resolution, reconciliation, discrepancy detection, persistence, auditability, and synthetic enterprise data simulation.

---

## Overview

Modern organizations often maintain overlapping business data across multiple systems. Differences in schemas, values, identifiers, and relationships can lead to duplicate records, missing data, incorrect financial information, and unreliable reporting.

This platform provides an automated pipeline for transforming raw enterprise data into validated and auditable reconciliation results.

```text
Enterprise Data Sources
          ↓
Data Ingestion & Validation
          ↓
Schema & Value Normalization
          ↓
Entity Resolution
          ↓
Cross-System Reconciliation
          ↓
Discrepancy Detection
          ↓
Business Metrics
          ↓
Persistence & Audit
```

---

## Key Capabilities

### Data Quality

* Missing-value detection
* Duplicate detection
* Schema and column validation
* Data-type validation
* Referential-integrity checks
* Numeric and financial sanity checks

### Cross-System Reconciliation

* Schema normalization
* Semantic column matching
* Value normalization
* Fuzzy entity resolution using **RapidFuzz**
* Field-level comparison
* Source-only and target-only record detection
* Reconciliation metrics

### Enterprise Data Simulation

The platform includes a deterministic synthetic enterprise environment, **NovaRetail Enterprise**, representing:

```text
Regions
Customers
Products
Orders
Invoices
Payments
Refunds
```

These datasets are transformed into simulated:

```text
CRM
ERP
Payment System
```

Controlled discrepancies can be injected into separate scenarios, including duplicate records, invalid references, incorrect invoice amounts, negative payments, and missing statuses.

### Scenario & Dataset Management

The platform provides:

* Clean and discrepant scenarios
* Machine-readable scenario manifests
* Scenario catalog
* Structured dataset registry
* Automated dataset profiling
* Row, column, null-rate, data-type, and uniqueness analysis

---

## Persistence & Audit

Reconciliation executions are persisted using **PostgreSQL and SQLAlchemy**.

The system tracks:

* Reconciliation runs
* Execution status
* Metrics
* Discrepancies
* Timestamps
* Audit records
* Failed executions

This provides traceability across the reconciliation lifecycle.

---

## REST API

Built with **FastAPI**.

```http
GET  /health/
POST /datasets/upload
POST /reconciliation/run
GET  /reconciliation/runs
GET  /reconciliation/runs/{run_id}
GET  /reconciliation/runs/{run_id}/audit
```

---

## Technology Stack

| Area              | Technologies           |
| ----------------- | ---------------------- |
| Backend           | Python, FastAPI        |
| Data Processing   | Pandas, NumPy          |
| Entity Resolution | RapidFuzz              |
| Database          | PostgreSQL, SQLAlchemy |
| Testing           | Pytest                 |
| Development       | Git, GitHub            |

---

## Testing

The project maintains an automated regression suite covering ingestion, validation, reconciliation, entity resolution, APIs, persistence, audit logging, synthetic data generation, scenario management, dataset registration, and profiling.

```text
160 passed
0 failed
1 warning
```

The remaining warning is a dependency deprecation warning from the FastAPI/Starlette testing stack and does not represent a test failure.

---

## Architecture

```text
                    Enterprise Data
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
       CRM               ERP          Payment System
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                 Data Quality Engine
                          │
                          ▼
                Entity Resolution
                          │
                          ▼
                 Reconciliation
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       Business Metrics          Audit & History
             │                         │
             └────────────┬────────────┘
                          ▼
                  Enterprise Data
                    Trust Platform
```

---

## Current Status

```text
✓ Backend Foundation
✓ Data Ingestion & Quality
✓ Core Reconciliation
✓ Persistence & Audit
✓ Enterprise Synthetic Data
✓ Multi-Source Simulation
✓ Scenario Management
✓ Dataset Registry & Profiling

→ Next: Advanced Data Quality Engine
```

**Current Release:** `phase-5.7-complete`
**Latest Commit:** `3e584c2`
**Branch:** `main`

---

## Roadmap

The platform is evolving toward an **AI-assisted Enterprise Data Trust Platform** with planned capabilities including:

* Advanced anomaly detection
* Explainable entity resolution
* Business-impact analysis
* Human-in-the-loop remediation
* AI-assisted investigation
* Enterprise monitoring dashboard
* Production-grade deployment

---

## Author

**Prajwal G N**

B.Tech Artificial Intelligence & Data Science
REVA University, Bengaluru, India

GitHub:
https://github.com/PrajwalGN-35

Project Repository:
https://github.com/PrajwalGN-35/enterprise-data-reconciliation-engine
