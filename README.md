# Enterprise Automated Data Quality & Cross-System Reconciliation Engine

An enterprise-style **data trust and cross-system reconciliation platform** designed to identify, explain, score, and track data inconsistencies across CRM, ERP, payment, and other heterogeneous business systems.

Built with **Python, FastAPI, Pandas, NumPy, RapidFuzz, PostgreSQL, SQLAlchemy, and Pytest**, the platform combines automated data-quality validation, entity resolution, cross-system reconciliation, anomaly detection, quality scoring, persistence, auditability, and deterministic enterprise data simulation.

---

## Overview

Modern organizations maintain overlapping business data across multiple systems. Differences in schemas, identifiers, values, formats, and relational dependencies can result in duplicate records, missing information, invalid references, financial inconsistencies, and unreliable reporting.

This platform provides an automated **data trust pipeline** that transforms raw enterprise data into validated, reconciled, scored, and auditable results.

```text
Enterprise Data Sources
          ↓
Data Ingestion & Validation
          ↓
Schema & Value Normalization
          ↓
Data Quality Assessment
          ↓
Entity Resolution
          ↓
Cross-System Reconciliation
          ↓
Discrepancy Detection
          ↓
Quality Scoring & Risk Classification
          ↓
Business Metrics
          ↓
Persistence & Audit
```

---

## Key Capabilities

### Data Quality

The platform provides automated quality assessment across multiple dimensions:

* Missing-value and completeness detection
* Duplicate and uniqueness detection
* Schema and column validation
* Data-type and format validation
* Referential-integrity checks
* Cross-field consistency validation
* Numeric and financial sanity checks
* Statistical anomaly detection
* Rule-level quality scoring
* Dataset-level quality scoring
* Risk classification

Quality results are categorized using deterministic risk levels:

```text
EXCELLENT
GOOD
FAIR
POOR
CRITICAL
```

---

## Cross-System Reconciliation

The reconciliation engine supports heterogeneous enterprise datasets through:

* Schema normalization
* Semantic column matching
* Value normalization
* Fuzzy entity resolution using **RapidFuzz**
* Field-level comparison
* Source-only record detection
* Target-only record detection
* Matched-record validation
* Discrepancy classification
* Reconciliation metrics
* Business-impact analysis

The system is designed to explain **what differs, where it differs, and how significant the discrepancy is** rather than simply returning a pass/fail result.

---

## Enterprise Data Simulation

The platform includes a deterministic synthetic enterprise environment called **NovaRetail Enterprise**.

It models a simplified business ecosystem containing:

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

Controlled data-quality defects can be injected into reproducible scenarios, including:

* Duplicate records
* Missing values
* Invalid references
* Incorrect invoice amounts
* Negative payments
* Missing statuses
* Cross-system value inconsistencies

This allows reconciliation and data-quality workflows to be tested against realistic enterprise-style scenarios without relying on confidential business data.

---

## Scenario & Dataset Management

The platform provides structured dataset and scenario management through:

* Clean and discrepant scenarios
* Machine-readable scenario manifests
* Scenario catalog
* Dataset registry
* Dataset metadata
* Automated dataset profiling
* Row and column statistics
* Null-rate analysis
* Data-type analysis
* Uniqueness analysis
* Reproducible discrepancy injection

The synthetic environment provides a controlled foundation for repeatable development, testing, and regression validation.

---

## Data Quality Engine

The data-quality subsystem is designed as a modular rule-based engine.

```text
Dataset
   ↓
Quality Rules
   ├── Completeness
   ├── Uniqueness
   ├── Validity
   ├── Referential Integrity
   ├── Cross-Field Consistency
   └── Statistical Anomaly Detection
          ↓
      Quality Issues
          ↓
      Quality Score
          ↓
     Risk Classification
          ↓
    Persistence & Audit
```

The scoring engine produces deterministic, dashboard-ready results containing:

* Overall quality score
* Risk classification
* Rule count
* Failed-rule count
* Rule-level scores
* Issue counts
* Affected-row counts
* Impact measurements

---

## Persistence & Audit

Reconciliation and quality executions are persisted using **PostgreSQL and SQLAlchemy**.

The system tracks:

* Reconciliation runs
* Data-quality assessments
* Quality runs
* Execution status
* Quality scores
* Risk classifications
* Rule-level results
* Discrepancies
* Business metrics
* Timestamps
* Audit records
* Failed executions

This provides traceability across the complete reconciliation and data-quality lifecycle.

---

## REST API

The backend is implemented using **FastAPI**.

### Core Endpoints

```text
GET  /health/

POST /datasets/upload

POST /reconciliation/run
GET  /reconciliation/runs
GET  /reconciliation/runs/{run_id}
GET  /reconciliation/runs/{run_id}/audit
```

### Data Quality Endpoints

```text
POST /quality/profile
POST /quality/validate
POST /quality/run

GET  /quality/runs
GET  /quality/runs/{run_id}
GET  /quality/runs/{run_id}/issues
GET  /quality/runs/{run_id}/score
```

The API provides both **stateless quality analysis** and **persisted quality-run workflows**.

---

## Technology Stack

| Area              | Technologies           |
| ----------------- | ---------------------- |
| Backend           | Python, FastAPI        |
| Data Processing   | Pandas, NumPy          |
| Entity Resolution | RapidFuzz              |
| Database          | PostgreSQL, SQLAlchemy |
| Testing           | Pytest                 |
| Version Control   | Git, GitHub            |

---

## Testing & Reliability

The project maintains a comprehensive automated regression suite covering:

* Data ingestion
* File validation
* Schema validation
* Data profiling
* Data-quality rules
* Completeness analysis
* Duplicate detection
* Validity checks
* Referential integrity
* Cross-field consistency
* Statistical anomaly detection
* Quality scoring
* Risk classification
* Quality persistence
* Reconciliation workflows
* Entity resolution
* REST APIs
* Database persistence
* Audit logging
* Synthetic enterprise data
* Scenario management
* Dataset registry
* Dataset profiling
* API contracts
* Regression and compatibility checks

### Current Regression Status

```text
287 passed
0 failed
1 warning
```

The remaining warning is a dependency deprecation warning from the FastAPI/Starlette testing stack and does not represent a test failure.

---

## Architecture

```text
                         Enterprise Data
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
            CRM                ERP          Payment System
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                     Ingestion & Validation
                                │
                                ▼
                     Schema & Normalization
                                │
                                ▼
                       Data Quality Engine
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
             Quality Rules  Entity Resolution  Anomaly Detection
                  │             │             │
                  └─────────────┼─────────────┘
                                ▼
                        Reconciliation Engine
                                │
                                ▼
                       Discrepancy Detection
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
              Quality Scoring          Business Metrics
                    │                       │
                    └───────────┬───────────┘
                                ▼
                       Persistence & Audit
                                │
                                ▼
                    Enterprise Data Trust
                           Platform
```

---

## Current Status

```text
✓ Backend Foundation
✓ Data Ingestion & Validation
✓ Data Profiling
✓ Core Reconciliation
✓ Entity Resolution
✓ Discrepancy Detection
✓ Persistence & Audit
✓ Enterprise Synthetic Data
✓ Multi-Source Simulation
✓ Scenario Management
✓ Dataset Registry & Profiling
✓ Advanced Data Quality Engine
✓ Completeness & Missing Data
✓ Duplicate & Uniqueness Detection
✓ Validity & Domain Rules
✓ Referential & Cross-Field Validation
✓ Statistical Anomaly Detection
✓ Quality Scoring
✓ Risk Classification
✓ Quality Assessment Persistence
✓ Automated Quality Workflow Integration
✓ Standalone Data Quality API
✓ Enterprise Regression Hardening
✓ Phase 6 Integration & Release

→ Next: Phase 7
```

---

## Release History

The project is developed through structured Git checkpoints and release tags.

### Latest Release

```text
Release: phase-6.13-complete
Commit:  afd8eee4834df02264e4d3f0a5ce349a90797ac9
Branch:  main
Tests:   287 passed
Status:  Production-ready development checkpoint
```

Phase 6.13 represents the completed integration and release-hardening checkpoint for the Data Quality platform.

---

## Roadmap

The platform is evolving toward an **AI-assisted Enterprise Data Trust Platform**.

Planned capabilities include:

* Advanced explainable anomaly detection
* Explainable entity resolution
* Business-impact analysis
* Human-in-the-loop remediation
* AI-assisted discrepancy investigation
* Data-quality monitoring
* Enterprise analytics dashboard
* Historical quality trend analysis
* Automated remediation workflows
* Production-grade deployment
* Enterprise observability

---

## Author

**Prajwal G N**

B.Tech Artificial Intelligence & Data Science
REVA University, Bengaluru, India

**GitHub:**
https://github.com/PrajwalGN-35

**Project Repository:**
https://github.com/PrajwalGN-35/enterprise-data-reconciliation-engine

---

## Project Status

**Enterprise Data Quality & Cross-System Reconciliation Engine**
**Phase 6 — Complete**

```text
287 automated tests
0 test failures
Phase 6.13 released
GitHub main synchronized
Release tag verified
Working tree clean
```
