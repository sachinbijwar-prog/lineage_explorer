# Architecture.md

# Enterprise Dependency & Lineage Explorer

## POC Architecture

### Purpose

The Enterprise Dependency & Lineage Explorer provides a metadata-driven visualization platform for understanding enterprise data lineage and dependencies.

This document defines the approved architecture for the Proof of Concept (POC).

---

# High-Level Architecture

```text
User
  |
  v
React UI (TypeScript + Vite)
  |
  v
FastAPI Backend
  |
  v
Metadata Service
  |
  v
JSON Metadata Repository
```

---

# Frontend Layer

Technology:

* React
* TypeScript
* Vite
* Cytoscape.js

Responsibilities:

* Render lineage graph
* Search nodes
* Display node details
* Execute lineage traversal
* Perform impact analysis visualization

---

# Backend Layer

Technology:

* FastAPI
* Python 3.12
* Pydantic

Responsibilities:

* Serve metadata APIs
* Build lineage graph payloads
* Execute traversal logic
* Provide impact analysis APIs

---

# Metadata Layer

POC Storage:

* JSON files

Example:

```text
backend/data/metadata.json
```

Responsibilities:

* Store nodes
* Store relationships
* Act as metadata source for graph generation

---

# Graph Model

## Node Types

* Source
* Table
* File
* Job
* Pipeline
* Report
* Dashboard

## Relationship Types

* Reads_From
* Writes_To
* Produces
* Consumes

---

# Current POC Flow

```text
Sales Orders
      |
      v
Transaction
      |
      v
Summary
```

The graph currently demonstrates:

* Source system
* Transformation layer
* Reporting layer

---

# Future Architecture (Out of Scope for POC)

The following components are future enhancements and must NOT be implemented during the current POC:

* Neo4j
* OpenLineage
* Apache Atlas
* DataHub
* Airflow Metadata Scanner
* Hive Metadata Scanner
* Spark Metadata Scanner
* Enterprise Authentication
* Multi-Tenancy

---

# Development Principles

1. Metadata Driven
2. API First
3. Simple Before Complex
4. Visualization First
5. Extensible Design
6. No Premature Optimization

---

# Approved Technology Stack

Frontend

* React
* TypeScript
* Cytoscape.js

Backend

* FastAPI
* Python 3.12
* Pydantic

Metadata

* JSON

Future

* Neo4j

---

# Current Development Phase

Phase 1

Metadata-Driven Visualization

Goal:

Replace hardcoded graph data with metadata served through FastAPI APIs.

```
```
