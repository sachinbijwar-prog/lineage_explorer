# POC_IMPLEMENTATION_SPEC.md

# Enterprise Dependency & Lineage Explorer

## POC Implementation Specification

**Version:** 0.2

**Author:** Sachin Bijwar

**Status:** Active Development

**Last Updated:** June 2026

---

# 1. Objective

Build a metadata-driven Enterprise Dependency & Lineage Explorer that enables users to visualize, search, traverse, and analyze end-to-end data lineage across enterprise data platforms.

The POC should demonstrate the core concepts of:

* Lineage visualization
* Dependency discovery
* Impact analysis
* Metadata-driven graph generation
* Interactive exploration

The solution must be lightweight, easy to demo, and extensible for future enterprise-scale implementation.

---

# 2. Business Problem

Enterprise data ecosystems contain hundreds of interconnected components:

* Source systems
* Batch jobs
* ETL pipelines
* Data warehouses
* Data marts
* Reports
* Dashboards

Understanding upstream and downstream dependencies is difficult.

The objective is to provide a single interface that allows users to:

* Understand data flow
* Trace lineage
* Analyze impact of changes
* Explore dependencies visually

---

# 3. POC Scope

## In Scope

### Metadata Management

* Metadata repository (backed by Neo4j)
* Metadata ingestion APIs (taking JSON payloads)
* Metadata-driven graph generation

### Visualization

* Interactive lineage graph
* Node highlighting
* Relationship traversal
* Search

### Analysis

* Upstream lineage
* Downstream lineage
* Impact analysis

### User Experience

* Graph exploration
* Node details panel
* Search interface

---

## Out of Scope

The following are intentionally excluded from the POC:

### Security

* Authentication
* Authorization
* SSO

### Enterprise Features

* Multi-tenancy
* Auditing
* Workflow approvals
* Notifications

### Integrations

* OpenLineage
* Atlas
* DataHub
* Collibra
* Informatica

### Runtime Metadata Collection

* Hive scanning
* Spark scanning
* Airflow scanning
* Cron scanning

### Infrastructure

* Kubernetes deployment
* Cloud deployment
* Production monitoring

---

# 4. Technology Stack

## Frontend

* React
* TypeScript
* Vite
* Cytoscape.js (or React Flow as referenced in the tracker)

## Backend

* FastAPI
* Python 3.12
* Pydantic

## Metadata Storage (POC & Future)

* Neo4j Graph Database (for relationships & lineage traversal)
* PostgreSQL (for application metadata & configuration)

---

# 6. Target Architecture

```text
User
  |
  v
React UI (Cytoscape/React Flow)
  |
  v
FastAPI API Layer
  |
  v
Metadata Service (Graph Service)
  |
  v
Neo4j Graph Database
```

---

# 7. Data Model

## Node (stored as :Asset or :Process in Neo4j)

Attributes:

* id (unique string)
* name
* type (Source, Table, File, Job, Pipeline, Report, Dashboard)
* description
* owner
* system
* tags

---

## Edge (Relationships in Neo4j)

Attributes:

* source
* target
* relationship_type (READ_BY, WRITES_TO, Reads_From, Writes_To, Produces, Consumes)

---

# 8. Functional Requirements

## FR-01 Metadata API

Provide API to retrieve lineage metadata.

Endpoints:

GET /api/v1/lineage

GET /api/v1/node/{id}

POST /api/v1/lineage/seed

POST /api/v1/lineage/upload (Ingest JSON metadata payload into Neo4j)

---

## FR-02 Graph Visualization

Display lineage graph.

Requirements:

* Zoom
* Pan
* Fit to screen
* Click node

---

## FR-03 Node Details

When user clicks a node:

Display:

* Name
* Type
* Description
* Owner
* Upstream Count
* Downstream Count

---

## FR-04 Search

Search graph nodes by:

* Name
* Type

Behavior:

* Highlight matching node
* Center graph on node

---

## FR-05 Upstream Traversal

Show all upstream dependencies using native Cypher path queries.

---

## FR-06 Downstream Traversal

Show all downstream dependencies using native Cypher path queries.

---

## FR-07 Impact Analysis

Given a selected node:

Display all affected downstream objects and highlight the impacted path.

---

# 9. POC Metadata Ingestion Format

Metadata is uploaded as JSON via `/api/v1/lineage/upload` and persisted in Neo4j:

```json
{
  "nodes": [
    {
      "id": "sales_orders",
      "name": "Sales Orders",
      "type": "Source"
    },
    {
      "id": "transaction",
      "name": "Transaction",
      "type": "Table"
    },
    {
      "id": "summary",
      "name": "Summary",
      "type": "Report"
    }
  ],
  "edges": [
    {
      "source": "sales_orders",
      "target": "transaction",
      "relationship_type": "Reads_From"
    },
    {
      "source": "transaction",
      "target": "summary",
      "relationship_type": "Writes_To"
    }
  ]
}
```

---

# 10. Development Phases

## Phase 1 - Metadata Driven Visualization

Goal:

Replace hardcoded graph with Neo4j metadata-driven graph.

Tasks:

* Metadata Pydantic models
* Ingestion/Upload API for JSON metadata payloads
* Neo4j Metadata Repository Service
* Lineage query API returning nodes and edges from Neo4j
* Dynamic graph rendering on the frontend

Success Criteria:

Frontend graph loads nodes and relationships dynamically from the Neo4j database.

---

## Phase 2 - Interactive Exploration

Tasks:

* Node details panel
* Search
* Highlighting
* Graph navigation

Success Criteria:

User can explore the graph, search for nodes, and view properties interactively.

---

## Phase 3 - Lineage Analysis

Tasks:

* Upstream traversal (Cypher query)
* Downstream traversal (Cypher query)
* Impact analysis (Cypher query)

Success Criteria:

User can perform interactive dependency and impact analysis queries.

---

## Phase 4 - POC Hardening

Tasks:

* Error handling
* Loading states
* Documentation cleanup
* UI improvements

Success Criteria:

Demo-ready application showing real-time impact analysis and lineage tracing.

---

# 11. Coding Standards

## Backend

* Python 3.12
* Type hints required
* Pydantic models required
* Keep files under 300 lines where practical

## Frontend

* TypeScript
* Functional components only
* React hooks

## General

* Clear naming conventions
* No dead code
* No premature optimization
* Simplicity preferred over abstraction

---

# 12. AI Agent Operating Instructions

The AI development agent must follow these rules:

1. Do not redesign architecture (stick to FastAPI + Neo4j as aligned by ADR-006).
2. Do not introduce new frameworks.
3. Implement one task at a time.
4. Update documentation after each completed task.
5. Preserve existing functionality.
6. Keep the implementation simple.
7. POC objectives take precedence over enterprise features.
8. Stop after completing each task and provide a summary.

---

# 13. Current Development Priority

Next Task:

## Task-01

Create Metadata Model, Ingestion API, and Neo4j Repository Service

Deliverables:

* Pydantic models for graph input/output
* JSON upload/ingest API endpoint (`/api/v1/lineage/upload`)
* Repository service layer matching Neo4j data model
* Lineage retrieval API endpoint (`/api/v1/lineage`) fetching from Neo4j

Success Criteria:

Frontend loads dynamic lineage metadata returned from the Neo4j API.

---

END OF DOCUMENT
