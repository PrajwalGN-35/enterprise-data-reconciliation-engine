# Enterprise Automated Data Quality & Cross-System Reconciliation Engine

An enterprise-style automated data quality and cross-system reconciliation platform designed to ingest heterogeneous datasets, validate data quality, normalize schemas and values, resolve matching entities, detect field-level discrepancies, calculate reconciliation metrics, and maintain persistent audit history.

Built with **Python, FastAPI, Pandas, RapidFuzz, PostgreSQL, SQLAlchemy, and Pytest**, the system follows a modular backend architecture with automated testing and persistent reconciliation tracking.

---

## Overview

Organizations often maintain the same business data across multiple systems such as ERP, CRM, databases, APIs, CSV files, and Excel workbooks. Differences between these systems can result in inconsistent records, duplicate entities, incorrect reporting, and data-quality issues.

This project automates the reconciliation process by comparing source and target datasets through a structured pipeline:

```text
Source Dataset + Target Dataset
              ↓
       Dataset Ingestion
              ↓
    Data Quality Validation
              ↓
      Schema Normalization
              ↓
   Semantic Column Matching
              ↓
      Value Normalization
              ↓
       Entity Resolution
              ↓
  Field-Level Reconciliation
              ↓
    Discrepancy Detection
              ↓
    Reconciliation Metrics
              ↓
   PostgreSQL Persistence
              ↓
      Audit & Run History
```

---

# Key Features

### Dataset Ingestion

Supports structured dataset ingestion for:

* CSV
* XLSX
* JSON

The ingestion layer validates incoming datasets before they enter the reconciliation workflow.

### Data Quality Validation

Automated validation includes:

* Missing-value detection
* Duplicate detection
* Column validation
* Data-type inspection
* Dataset structure validation
* Input validation

### Schema Normalization

Handles structural differences between source and target datasets through:

* Column-name normalization
* Schema comparison
* Semantic column matching
* Data-type handling
* Value normalization

### Entity Resolution

Uses **RapidFuzz** to identify corresponding records when the same entity is represented differently across systems.

Example:

```text
Source:  "Raj Kumar"
Target:  "Rajkumar"

        ↓

Fuzzy Entity Match
```

### Field-Level Reconciliation

Matched records are compared at the field level to identify:

* Matching values
* Mismatched values
* Missing values
* Source-only records
* Target-only records
* Field-specific discrepancies

### Reconciliation Metrics

The engine calculates:

* Total records
* Matched records
* Unmatched records
* Reconciled records
* Exception records
* Reconciliation percentage
* Exception percentage
* Field-level discrepancy counts

---

# Persistence & Audit System

Phase 4 introduced persistent reconciliation tracking using **PostgreSQL and SQLAlchemy**.

Each reconciliation execution follows a tracked lifecycle:

```text
RUNNING
   │
   ├── SUCCESS → COMPLETED
   │
   └── FAILURE → FAILED
```

The database stores:

* Reconciliation run ID
* Source dataset name
* Target dataset name
* Execution status
* Start timestamp
* Completion timestamp
* Reconciliation metrics
* Discrepancy statistics

### Audit Logging

The system creates audit records for reconciliation executions, including:

* Action
* Entity type
* Entity ID
* Execution status
* Dataset information
* Error information for failures
* Timestamp

Failed reconciliation executions are also persisted, ensuring that failures remain traceable instead of being silently discarded.

---

# REST API

The backend is implemented using **FastAPI**.

### Reconciliation

```http
POST /reconciliation/run
```

Runs reconciliation between source and target datasets.

### Reconciliation History

```http
GET /reconciliation/runs
```

Retrieves historical reconciliation runs with pagination.

```http
GET /reconciliation/runs/{run_id}
```

Retrieves detailed information about a specific reconciliation run.

```http
GET /reconciliation/runs/{run_id}/audit
```

Retrieves audit records associated with a reconciliation run.

### Dataset Upload

```http
POST /datasets/upload
```

Uploads and validates supported datasets.

### Health Check

```http
GET /health/
```

Checks backend availability.

---

# Testing

The project uses **Pytest** for automated testing across the reconciliation pipeline.

Test coverage includes:

* Dataset ingestion
* Data-quality validation
* Schema processing
* Entity resolution
* Reconciliation logic
* API behavior
* Database persistence
* Audit logging
* Reconciliation history
* Pagination
* Validation errors
* Failure handling
* Edge cases
* Regression testing

## Current Test Status

```text
115 passed
2 warnings
0 failed
```

The two warnings are dependency deprecation warnings from the FastAPI/Starlette testing stack and do not represent test failures.

---

# Technology Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL

### Data Processing

* Pandas
* RapidFuzz

### Testing

* Pytest
* FastAPI TestClient

### Development

* Git
* GitHub
* Python Virtual Environment

---

# Project Structure

```text
enterprise-reconciliation-engine/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── datasets.py
│   │   │   ├── reconciliation.py
│   │   │   ├── reconciliation_history_schemas.py
│   │   │   └── reconciliation_schemas.py
│   │   │
│   │   ├── core/
│   │   │   ├── database.py
│   │   │   ├── db_init.py
│   │   │   └── config.py
│   │   │
│   │   ├── models/
│   │   │   ├── reconciliation.py
│   │   │   └── __init__.py
│   │   │
│   │   └── ...
│   │
│   ├── tests/
│   │   ├── test_persistence_foundation.py
│   │   ├── test_persistence_integration.py
│   │   ├── test_reconciliation_history_api.py
│   │   ├── test_reconciliation_history_edge_cases.py
│   │   ├── test_reconciliation_persistence_hardening.py
│   │   └── ...
│   │
│   └── requirements.txt
│
├── data/
│   ├── sample/
│   └── uploads/
│
└── README.md
```

---

# Development Phases Completed

## Phase 1 — Backend Foundation

* FastAPI application foundation
* Backend project structure
* Configuration
* Initial API setup

**Status: Completed**

## Phase 2 — Data Ingestion & Quality

* Dataset upload
* CSV/XLSX processing
* Dataset profiling
* Data-quality checks
* Input validation
* Automated testing

**Status: Completed**

## Phase 3 — Core Reconciliation Engine

* Schema normalization
* Semantic column matching
* Value normalization
* Fuzzy entity resolution
* Field-level discrepancy detection
* Reconciliation metrics
* End-to-end workflow
* Reconciliation API
* Automated testing

**Status: Completed**

## Phase 4 — Persistence, Audit & Run History

* PostgreSQL persistence
* SQLAlchemy data models
* Reconciliation run lifecycle
* Persistent run history
* Audit logging
* Failed-run persistence
* Failure handling
* Reconciliation history APIs
* Pagination
* Validation and edge-case testing

**Status: Completed**

### Phase 4 Release

```text
Release: phase-4-complete
Branch: main
Automated Tests: 115 passed
```

---

# Engineering Workflow

Development follows a structured engineering process:

```text
Plan
  ↓
Implement
  ↓
Test
  ↓
Fix
  ↓
Commit
  ↓
Document
```

Each development phase is maintained through structured Git commits and release checkpoints.

---

# Project Status

```text
Phase 1 — Backend Foundation              ✓
Phase 2 — Data Ingestion & Quality        ✓
Phase 3 — Core Reconciliation Engine      ✓
Phase 4 — Persistence & Audit             ✓

Automated Tests                            115 PASS
Current Release                            phase-4-complete
Primary Branch                             main
```

---

# Author

**Prajwal G N**

B.Tech Artificial Intelligence & Data Science
REVA University, Bengaluru, India

GitHub:
https://github.com/PrajwalGN-35

Project Repository:
https://github.com/PrajwalGN-35/enterprise-data-reconciliation-engine
